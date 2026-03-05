from django.core.management.base import BaseCommand
from django.conf import settings
from school.telegram import send_telegram_message
import requests


class Command(BaseCommand):
    help = 'Тестирование отправки сообщений в Telegram'

    def handle(self, *args, **options):
        self.stdout.write("=== ТЕСТИРОВАНИЕ TELEGRAM ===\n")

        # Проверка настроек
        self.stdout.write(f"TELEGRAM_BOT_TOKEN: {settings.TELEGRAM_BOT_TOKEN}")
        self.stdout.write(f"TELEGRAM_CHAT_ID: {settings.TELEGRAM_CHAT_ID}")

        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
            self.stdout.write(self.style.ERROR("❌ Настройки не заполнены в settings.py"))
            return

        # Проверка токена
        self.stdout.write("\n1. Проверка токена бота...")
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getMe"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                bot_info = response.json()
                self.stdout.write(self.style.SUCCESS(f"   ✅ Бот найден: @{bot_info['result']['username']}"))
            else:
                self.stdout.write(self.style.ERROR(f"   ❌ Ошибка токена: {response.status_code}"))
                self.stdout.write(f"   Ответ: {response.text}")
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Ошибка подключения: {e}"))
            return

        # Проверка отправки
        self.stdout.write("\n2. Отправка тестового сообщения...")
        result = send_telegram_message(
            "<b>🔔 Тестовое сообщение</b>\n\nЕсли вы это видите, Telegram работает правильно!")

        if result:
            self.stdout.write(self.style.SUCCESS("   ✅ Сообщение отправлено! Проверьте Telegram."))
        else:
            self.stdout.write(self.style.ERROR("   ❌ Ошибка отправки сообщения"))

        # Проверка getUpdates
        self.stdout.write("\n3. Проверка получения обновлений...")
        updates_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getUpdates"
        try:
            response = requests.get(updates_url, timeout=5)
            if response.status_code == 200:
                updates = response.json()
                if updates['ok'] and updates['result']:
                    self.stdout.write(self.style.SUCCESS(f"   ✅ Найдено {len(updates['result'])} обновлений"))
                    for update in updates['result'][-3:]:  # Покажем последние 3
                        if 'message' in update:
                            chat_id = update['message']['chat']['id']
                            username = update['message']['chat'].get('username', 'нет username')
                            first_name = update['message']['chat'].get('first_name', '')
                            self.stdout.write(f"      • Чат ID: {chat_id} - @{username} {first_name}")
                else:
                    self.stdout.write(self.style.WARNING("   ⚠️ Нет обновлений. Напишите боту любое сообщение."))
            else:
                self.stdout.write(self.style.ERROR(f"   ❌ Ошибка получения обновлений: {response.status_code}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Ошибка: {e}"))