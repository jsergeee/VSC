# school/bot_service.py — полная исправленная версия

import json
import logging
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from .models import BotConfig, BotMessage, User, BotSubscriber

logger = logging.getLogger(__name__)

class MaxBotService:
    """
    Полноценный сервис для работы с чат-ботами в Max
    """

    def __init__(self, bot_id=None):
        self.bot = None
        if bot_id:
            try:
                self.bot = BotConfig.objects.get(id=bot_id, is_active=True, platform='max')
            except BotConfig.DoesNotExist:
                logger.warning(f"Бот с ID {bot_id} не найден или неактивен")

    def get_active_bot(self):
        """Возвращает первый активный бот Max"""
        if self.bot:
            return self.bot
        try:
            self.bot = BotConfig.objects.filter(platform='max', is_active=True).first()
            return self.bot
        except BotConfig.DoesNotExist:
            logger.warning("Активный бот Max не найден")
            return None

    def get_user_chat_id(self, user):
        """Получает chat_id пользователя (из профиля)"""
        if hasattr(user, 'telegram_chat_id') and user.telegram_chat_id:
            return user.telegram_chat_id

        if hasattr(user, 'student_profile'):
            return user.telegram_chat_id

        return None

    # ============================================================
    # ✅ МЕТОД handle_webhook — ОБРАБОТКА ВХОДЯЩИХ СООБЩЕНИЙ
    # ============================================================
    def handle_webhook(self, data):
        """
        Обрабатывает входящие сообщения из MAX и сохраняет подписчиков

        Args:
            data: данные из вебхука (dict)
        """
        try:
            logger.info("📨 Обработка вебхука в MaxBotService")
            logger.info(f"📨 Данные: {data}")

            # Извлекаем данные из вебхука
            message = data.get('message', {})
            recipient = message.get('recipient', {})
            sender = message.get('sender', {})
            body = message.get('body', {})
            
            chat_id = recipient.get('chat_id')
            user_id = sender.get('user_id')
            first_name = sender.get('first_name', '')
            last_name = sender.get('last_name', '')
            username = sender.get('username', '')
            text = body.get('text', '')
            update_type = data.get('update_type', '')

            # ✅ ПЫТАЕМСЯ НАЙТИ ПОЛЬЗОВАТЕЛЯ ПО user_id
            user = None
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    # Пробуем найти по chat_id (если сохраняли ранее)
                    subscriber = BotSubscriber.objects.filter(chat_id=str(chat_id)).first()
                    if subscriber and subscriber.user:
                        user = subscriber.user
                    else:
                        # Пробуем найти по username
                        if username:
                            try:
                                user = User.objects.get(username=username)
                            except User.DoesNotExist:
                                pass
                except Exception as e:
                    logger.warning(f"Ошибка поиска пользователя: {e}")

            # ✅ СОХРАНЯЕМ ПОДПИСЧИКА
            if chat_id:
                subscriber, created = BotSubscriber.objects.get_or_create(
                    chat_id=str(chat_id),
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'username': username,
                        'user': user if user else None,  
                    }
                )
                if user:
                # Обновляем max_chat_id у пользователя
                    if not user.max_chat_id:
                        user.max_chat_id = str(chat_id)
                        user.save()
                        logger.info(f"✅ Привязан MAX chat_id {chat_id} к пользователю {user.get_full_name()}")
                
                # Если подписчик найден и пользователь не привязан, привязываем
                if user and not subscriber.user:
                    subscriber.user = user
                
                # Обновляем данные при каждом сообщении
                if not created:
                    subscriber.last_activity = timezone.now()
                    if first_name:
                        subscriber.first_name = first_name
                    if last_name:
                        subscriber.last_name = last_name
                    if username:
                        subscriber.username = username
                    if user and not subscriber.user:
                        subscriber.user = user
                
                subscriber.save()
                logger.info(f"✅ Подписчик сохранен: {first_name} ({chat_id})")
                if subscriber.user:
                    logger.info(f"   👤 Привязан к пользователю: {subscriber.user.get_full_name()} ({subscriber.user.id})")

                # Находим бота
                bot = self.get_active_bot()
                if bot:
                    # Сохраняем входящее сообщение в лог
                    BotMessage.objects.create(
                        bot=bot,
                        direction='incoming',
                        sender=str(chat_id),
                        message=text[:500],
                        metadata={
                            'update_type': update_type,
                            'sender_id': user_id,
                            'sender_name': first_name,
                            'full_data': data
                        },
                        status='received'
                    )
                    logger.info(f"✅ Сохранено входящее сообщение от {chat_id}")

            # Обработка команд (если нужно)
            if text:
                self.process_command(bot, chat_id, text, first_name)

            return {'status': 'ok'}

        except Exception as e:
            logger.error(f"❌ Ошибка в handle_webhook: {e}")
            import traceback
            traceback.print_exc()
            return {'status': 'error', 'message': str(e)}

    # ============================================================
    # ✅ МЕТОД send_message — ОТПРАВКА СООБЩЕНИЙ (С ПРАВИЛЬНЫМИ ПАРАМЕТРАМИ)
    # ============================================================
    def send_message(self, chat_id, message, bot=None, buttons=None):
        """
        Отправляет сообщение через бота Max
        
        Args:
            chat_id: ID чата или пользователя (будет передан как query-параметр)
            message: текст сообщения
            bot: объект BotConfig (если None — берется первый активный)
            buttons: кнопки для интерактивных сообщений
        """
        from django.conf import settings
        
        bot = bot or self.get_active_bot()
        if not bot:
            logger.error("Бот не найден для отправки сообщения")
            return None
        
        # Сохраняем исходящее сообщение
        outgoing = BotMessage.objects.create(
            bot=bot,
            direction='outgoing',
            recipient=chat_id,
            message=message[:1000],
            status='pending'
        )
        
        try:
            api_url = getattr(settings, 'MAX_BOT_API_URL', None)
            if not api_url:
                error_msg = "MAX_BOT_API_URL не настроен в settings.py"
                logger.error(error_msg)
                outgoing.status = 'error'
                outgoing.response = error_msg
                outgoing.save()
                return None
            
            token = getattr(settings, 'MAX_BOT_TOKEN', None)
            if not token:
                error_msg = "MAX_BOT_TOKEN не настроен в settings.py"
                logger.error(error_msg)
                outgoing.status = 'error'
                outgoing.response = error_msg
                outgoing.save()
                return None
            
            # ✅ ПРАВИЛЬНО: chat_id как query-параметр
            params = {
                "chat_id": chat_id
            }
            
            # Формируем тело запроса (только текст и кнопки)
            payload = {
                'text': message,
            }
            
            if buttons:
                payload['attachments'] = [
                    {
                        'type': 'inline_keyboard',
                        'payload': {
                            'buttons': buttons
                        }
                    }
                ]
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': token,
            }
            
            logger.info(f"📤 Отправка сообщения в Max:")
            logger.info(f"   URL: {api_url}")
            logger.info(f"   Chat ID: {chat_id}")
            logger.info(f"   Message: {message[:50]}...")
            
            # ✅ Используем params для query-параметров
            response = requests.post(
                api_url,
                params=params,
                json=payload,
                headers=headers,
                timeout=10,
                verify=False  # Для разработки (в продакшене нужно убрать)
            )
            
            if response.status_code in [200, 201]:
                outgoing.status = 'sent'
                outgoing.response = response.text[:500]
                logger.info(f"✅ Сообщение отправлено в чат {chat_id}")
                logger.info(f"   Ответ: {response.text[:200]}")
            else:
                outgoing.status = 'failed'
                outgoing.response = f"Error {response.status_code}: {response.text[:200]}"
                logger.error(f"❌ Ошибка отправки: {response.status_code}")
                logger.error(f"   Ответ: {response.text}")
            
            outgoing.save()
            return outgoing
            
        except Exception as e:
            outgoing.status = 'error'
            outgoing.response = str(e)[:200]
            outgoing.save()
            logger.error(f"❌ Ошибка при отправке сообщения: {e}")
            import traceback
            traceback.print_exc()
            return None

    # ============================================================
    # 📬 МЕТОД send_broadcast — МАССОВАЯ РАССЫЛКА
    # ============================================================
    def send_broadcast(self, message, subscribers=None, buttons=None):
        """
        Отправляет сообщение всем подписчикам бота
        
        Args:
            message: текст сообщения
            subscribers: список подписчиков (если None — все активные)
            buttons: кнопки для интерактивных сообщений
        """
        from .models import BotSubscriber
        
        if subscribers is None:
            subscribers = BotSubscriber.objects.filter(is_active=True)
        
        success_count = 0
        error_count = 0
        errors = []
        
        total = subscribers.count()
        logger.info(f"📬 Начало рассылки: {total} подписчиков")
        
        for subscriber in subscribers:
            try:
                result = self.send_message(
                    chat_id=subscriber.chat_id,
                    message=message,
                    buttons=buttons
                )
                if result and result.status == 'sent':
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"{subscriber.chat_id}: {result.response if result else 'No response'}")
            except Exception as e:
                error_count += 1
                errors.append(f"{subscriber.chat_id}: {str(e)}")
                logger.error(f"Ошибка отправки подписчику {subscriber.chat_id}: {e}")
        
        logger.info(f"📬 Рассылка завершена: {success_count} успешно, {error_count} ошибок")
        return {
            'success': success_count,
            'errors': error_count,
            'error_list': errors[:20]  # Ограничиваем список ошибок
        }

    # ============================================================
    # ✅ МЕТОД process_command — ОБРАБОТКА КОМАНД
    # ============================================================
    def process_command(self, bot, chat_id, text, sender_name):
        """
        Обрабатывает команды из сообщений
        """
        logger.info(f"📨 Команда от {chat_id}: {text[:50]}")
        
        # Простая логика ответа на команды
        text_lower = text.lower().strip()
        
        if text_lower in ['привет', 'здравствуйте', 'hi', 'hello']:
            self.send_message(
                chat_id=chat_id,
                message=f"Здравствуйте, {sender_name or 'гость'}! 👋\n\nЯ бот школы «Плюс Прогресс». Чем могу помочь?"
            )
            return True
        
        if text_lower in ['помощь', 'help']:
            self.send_message(
                chat_id=chat_id,
                message="Я могу помочь вам с:\n"
                       "- 📚 информацией о предметах\n"
                       "- 📅 записью на пробный урок\n"
                       "- 📞 контактами школы\n\n"
                       "Просто напишите, что вас интересует!"
            )
            return True
        
        if text_lower in ['предметы', 'курсы']:
            self.send_message(
                chat_id=chat_id,
                message="📚 Мы преподаем:\n\n"
                       "🇬🇧 Английский язык\n"
                       "🇷🇺 Русский язык\n"
                       "📐 Математика\n"
                       "🧬 Биология\n"
                       "💻 Информатика\n"
                       "📖 История\n"
                       "🌍 Обществознание"
            )
            return True
        
        if text_lower in ['заявка', 'пробный урок', 'записаться']:
            self.send_message(
                chat_id=chat_id,
                message="📝 Чтобы записаться на пробный урок, заполните форму:\n\n"
                       "https://plusprogress.ru/#trial\n\n"
                       "Или напишите администратору: @plusprogress"
            )
            return True
        
        if text_lower in ['контакты', 'телефон']:
            self.send_message(
                chat_id=chat_id,
                message="📞 Свяжитесь с нами:\n\n"
                       "📱 Телефон: +7 (XXX) XXX-XX-XX\n"
                       "📧 Email: info@plusprogress.ru\n"
                       "💬 Telegram: @plusprogress\n"
                       "🌐 Сайт: https://plusprogress.ru"
            )
            return True
        
        # Если команда не распознана
        self.send_message(
            chat_id=chat_id,
            message="Я не совсем понял запрос. 🤔\n\n"
                   "Напишите:\n"
                   "• Привет — чтобы начать\n"
                   "• Помощь — список команд\n"
                   "• Предметы — узнать о курсах\n"
                   "• Заявка — записаться на урок\n"
                   "• Контакты — связаться с нами"
        )
        return True