import requests
import logging
from django.conf import settings
from .models import HomeworkSubmission

logger = logging.getLogger(__name__)


# school/telegram.py - добавьте в начало файла

class TelegramNotifier:
    """Класс для отправки уведомлений в Telegram"""

    def __init__(self):
        self.bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        self.bot = None

    def is_configured(self):
        """Проверяет, настроен ли бот"""
        return self.bot_token is not None

    def send_message_sync(self, chat_id, message, parse_mode='HTML'):
        """
        Синхронная отправка сообщения
        """
        if not self.is_configured():
            logger.warning("Telegram bot not configured")
            return False

        if not chat_id:
            logger.warning(f"No chat_id provided")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode,
        }

        try:
            response = requests.post(url, data=payload, timeout=5)
            response.raise_for_status()
            logger.info(f"Message sent to {chat_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending message to {chat_id}: {e}")
            return False
def send_telegram_message(text, parse_mode='HTML'):
    """
    Отправляет сообщение в общий Telegram чат (админский)
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning("Telegram не настроен: отсутствуют токен или chat_id")
        return False

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        'chat_id': settings.TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': parse_mode,
    }

    try:
        response = requests.post(url, data=payload, timeout=5)
        response.raise_for_status()
        logger.info(f"Telegram сообщение отправлено в общий чат: {text[:50]}...")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка отправки в Telegram (общий чат): {e}")
        return False


def send_telegram_message_to_user(user, text, parse_mode='HTML'):
    """
    Отправляет сообщение конкретному пользователю Telegram
    """
    if not user.telegram_chat_id:
        logger.warning(f"У пользователя {user.username} нет telegram_chat_id")
        return False

    if not user.telegram_notifications:
        logger.info(f"У пользователя {user.username} отключены уведомления")
        return False

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        'chat_id': user.telegram_chat_id,
        'text': text,
        'parse_mode': parse_mode,
    }

    try:
        response = requests.post(url, data=payload, timeout=5)
        response.raise_for_status()
        logger.info(f"Telegram сообщение отправлено пользователю {user.username}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка отправки в Telegram пользователю {user.username}: {e}")
        return False


def notify_new_lesson(lesson):
    """Уведомление о новом уроке"""
    # Отправляем в общий чат (админский)
    admin_text = f"""
<b>📚 Новый урок!</b>

👨‍🏫 Учитель: {lesson.teacher.user.get_full_name()}
👨‍🎓 Ученики: {', '.join([s.user.get_full_name() for s in lesson.students.all()])}
📅 Дата: {lesson.date}
⏰ Время: {lesson.start_time}
📖 Предмет: {lesson.subject.name}
"""
    send_telegram_message(admin_text)

    # Отправляем учителю, если у него включены уведомления
    teacher = lesson.teacher.user
    if hasattr(teacher, 'telegram_chat_id') and teacher.telegram_chat_id and teacher.telegram_notifications:
        teacher_text = f"""
<b>📚 У вас новый урок!</b>

👨‍🎓 Ученики: {', '.join([s.user.get_full_name() for s in lesson.students.all()])}
📅 Дата: {lesson.date}
⏰ Время: {lesson.start_time}
📖 Предмет: {lesson.subject.name}
"""
        send_telegram_message_to_user(teacher, teacher_text)

    # Отправляем ученикам
    for student in lesson.students.all():
        if hasattr(student.user,
                   'telegram_chat_id') and student.user.telegram_chat_id and student.user.telegram_notifications:
            student_text = f"""
<b>📚 У вас новый урок!</b>

👨‍🏫 Учитель: {lesson.teacher.user.get_full_name()}
📅 Дата: {lesson.date}
⏰ Время: {lesson.start_time}
📖 Предмет: {lesson.subject.name}
"""
            send_telegram_message_to_user(student.user, student_text)


def notify_lesson_completed(lesson, report=None):
    """Уведомление о завершении урока"""
    # Получаем список учеников
    students_list = []
    for attendance in lesson.attendance.filter(status='attended'):
        student = attendance.student
        students_list.append(f"{student.user.get_full_name()} ({attendance.cost}₽)")

    students_text = ', '.join(students_list) if students_list else 'нет учеников'

    # Считаем общую сумму
    total_cost = sum(attendance.cost for attendance in lesson.attendance.filter(status='attended'))
    teacher_payment = sum(
        attendance.teacher_payment_share for attendance in lesson.attendance.filter(status='attended'))

    # Общий текст для админского чата
    admin_text = f"""
<b>✅ УРОК ЗАВЕРШЕН!</b>

👨‍🏫 Учитель: {lesson.teacher.user.get_full_name()}
👨‍🎓 Ученики: {students_text}
📅 Дата: {lesson.date.strftime('%d.%m.%Y')}
⏰ Время: {lesson.start_time.strftime('%H:%M')} - {lesson.end_time.strftime('%H:%M')}
📖 Предмет: {lesson.subject.name}

💰 <b>ФИНАНСЫ:</b>
   • Оплачено учениками: {total_cost} ₽
   • Выплата учителю: {teacher_payment} ₽
   • Комиссия школы: {total_cost - teacher_payment} ₽

📝 Тема: {report.topic if report else 'Не указана'}
"""
    if report and report.homework:
        admin_text += f"\n📚 Домашнее задание: {report.homework[:100]}..."

    admin_text += f"\n\n🔗 Ссылка на отчет: http://127.0.0.1:8000/admin/school/lessonreport/{report.id if report else ''}/change/"

    # Отправляем в общий чат
    send_telegram_message(admin_text)

    # Отправляем учителю
    teacher = lesson.teacher.user
    if hasattr(teacher, 'telegram_chat_id') and teacher.telegram_chat_id and teacher.telegram_notifications:
        teacher_text = f"""
<b>✅ Ваш урок завершен!</b>

👨‍🎓 Ученики: {students_text}
📅 Дата: {lesson.date.strftime('%d.%m.%Y')}
⏰ Время: {lesson.start_time.strftime('%H:%M')} - {lesson.end_time.strftime('%H:%M')}
📖 Предмет: {lesson.subject.name}

💰 <b>ВАША ВЫПЛАТА:</b> {teacher_payment} ₽

📝 Тема: {report.topic if report else 'Не указана'}
"""
        if report and report.homework:
            teacher_text += f"\n📚 ДЗ: {report.homework[:100]}..."

        send_telegram_message_to_user(teacher, teacher_text)

    # Отправляем ученикам, которые были на уроке
    for attendance in lesson.attendance.filter(status='attended'):
        student = attendance.student.user
        if hasattr(student, 'telegram_chat_id') and student.telegram_chat_id and student.telegram_notifications:
            student_text = f"""
<b>✅ Урок завершен!</b>

👨‍🏫 Учитель: {lesson.teacher.user.get_full_name()}
📅 Дата: {lesson.date.strftime('%d.%m.%Y')}
⏰ Время: {lesson.start_time.strftime('%H:%M')} - {lesson.end_time.strftime('%H:%M')}
📖 Предмет: {lesson.subject.name}

💰 Списано с баланса: {attendance.cost} ₽

📝 Тема: {report.topic if report else 'Не указана'}
"""
            if report and report.homework:
                student_text += f"\n📚 Домашнее задание: {report.homework}"

            send_telegram_message_to_user(student, student_text)


def notify_payment(user, amount, payment_type):
    """Уведомление о платеже"""
    emoji = '💰' if payment_type == 'income' else '💸'
    type_text = 'пополнение' if payment_type == 'income' else 'списание'

    # Текст для админского чата
    admin_text = f"""
{emoji} <b>{type_text.title()}!</b>

👤 Пользователь: {user.get_full_name()}
💵 Сумма: {amount} ₽
📊 Текущий баланс: {user.get_balance()} ₽
"""
    send_telegram_message(admin_text)

    # Отправляем пользователю, если включены уведомления
    if hasattr(user, 'telegram_chat_id') and user.telegram_chat_id and user.telegram_notifications:
        user_text = f"""
{emoji} <b>{type_text.title()}!</b>

💵 Сумма: {amount} ₽
📊 Ваш текущий баланс: {user.get_balance()} ₽
"""
        send_telegram_message_to_user(user, user_text)


def notify_homework_submitted(homework):
    """Уведомление о сданном ДЗ"""
    # Получаем последнюю сдачу
    try:
        submission = homework.submissions.latest('submitted_at')
        submitted_time = submission.submitted_at.strftime('%d.%m.%Y %H:%M')
    except (AttributeError, HomeworkSubmission.DoesNotExist):
        submitted_time = 'Неизвестно'
        submission = None
    
    # Текст для админского чата
    admin_text = f"""
<b>📤 Сдано домашнее задание!</b>

👨‍🎓 Ученик: {homework.student.user.get_full_name()}
📚 Задание: {homework.title}
⏰ Сдано: {submitted_time}
"""
    send_telegram_message(admin_text)

    # Отправляем учителю
    teacher = homework.teacher.user
    if teacher.telegram_chat_id and teacher.telegram_notifications:
        teacher_text = f"""
<b>📤 Ваш ученик сдал ДЗ!</b>

👨‍🎓 Ученик: {homework.student.user.get_full_name()}
📚 Задание: {homework.title}
⏰ Сдано: {submitted_time}
"""
        send_telegram_message_to_user(teacher, teacher_text)

def check_telegram_updates():
    """Проверяет новые сообщения от пользователей"""
    import requests
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getUpdates"

    try:
        response = requests.get(url)
        data = response.json()

        if data['ok'] and data['result']:
            print("\n📱 НОВЫЕ СООБЩЕНИЯ В TELEGRAM:")
            for update in data['result']:
                if 'message' in update:
                    msg = update['message']
                    chat_id = msg['chat']['id']
                    first_name = msg['from'].get('first_name', '')
                    username = msg['from'].get('username', '')
                    text = msg.get('text', '')

                    print(f"   ID: {chat_id}")
                    print(f"   Имя: {first_name}")
                    print(f"   Username: @{username}")
                    print(f"   Текст: {text}")
                    print("-" * 40)

                    # Здесь можно автоматически сохранять ID в базу
                    # find_and_update_user_by_telegram(chat_id, username, first_name)
        else:
            print("📭 Новых сообщений нет")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


def notify_new_homework(homework):
    """
    Отправляет уведомление о новом домашнем задании ученику
    """
    print(f"\n{'=' * 60}")
    print(f"🔔 ФУНКЦИЯ notify_new_homework ВЫЗВАНА для ДЗ #{homework.id}")
    print(f"   Задание: {homework.title}")
    print(f"   Ученик: {homework.student.user.get_full_name()}")
    print(f"   Дедлайн: {homework.deadline}")
    print(f"{'=' * 60}")

    # Проверяем наличие BASE_URL
    base_url = getattr(settings, 'BASE_URL', None)
    if not base_url:
        print(f"❌ BASE_URL не настроен в settings.py")
        logger.warning("BASE_URL not configured")
        return False

    notifier = TelegramNotifier()

    if not notifier.is_configured():
        print(f"❌ Telegram bot не настроен")
        logger.warning("Telegram bot not configured")
        return False

    student = homework.student
    teacher = homework.teacher

    # Проверяем, включены ли уведомления у ученика
    if not student.user.telegram_notifications or not student.user.telegram_chat_id:
        print(f"⚠️ У ученика {student.user.username} не включены Telegram уведомления или нет chat_id")
        return False

    # Форматируем дату
    deadline_str = homework.deadline.strftime('%d.%m.%Y %H:%M')

    # Формируем сообщение для ученика СО ССЫЛКОЙ
    message = (
        f"📝 <b>Новое домашнее задание</b>\n\n"
        f"<b>Предмет:</b> {homework.subject.name}\n"
        f"<b>Учитель:</b> {teacher.user.get_full_name()}\n"
        f"<b>Название:</b> {homework.title}\n"
        f"<b>Описание:</b> {homework.description[:200]}{'...' if len(homework.description) > 200 else ''}\n"
        f"<b>Срок сдачи:</b> {deadline_str}\n\n"
        f"🔗 <a href='{base_url}/student/homework/{homework.id}/'>Перейти к заданию</a>"
    )

    # Отправляем сообщение ученику
    result = notifier.send_message_sync(student.user.telegram_chat_id, message)
    print(f"   Результат отправки ученику: {'✅ УСПЕШНО' if result else '❌ ОШИБКА'}")

    # Уведомление учителю (опционально)
    if teacher.user.telegram_notifications and teacher.user.telegram_chat_id:
        teacher_message = (
            f"✅ <b>Домашнее задание создано</b>\n\n"
            f"<b>Ученик:</b> {student.user.get_full_name()}\n"
            f"<b>Предмет:</b> {homework.subject.name}\n"
            f"<b>Название:</b> {homework.title}\n"
            f"<b>Срок сдачи:</b> {deadline_str}"
        )
        notifier.send_message_sync(teacher.user.telegram_chat_id, teacher_message)

    # ✅ ДОБАВЛЯЕМ ОТПРАВКУ В ОБЩИЙ АДМИНСКИЙ ЧАТ
    try:
        admin_message = (
            f"📝 <b>Новое домашнее задание</b>\n\n"
            f"👨‍🎓 <b>Ученик:</b> {student.user.get_full_name()}\n"
            f"👨‍🏫 <b>Учитель:</b> {teacher.user.get_full_name()}\n"
            f"📚 <b>Предмет:</b> {homework.subject.name}\n"
            f"📝 <b>Задание:</b> {homework.title}\n"
            f"⏰ <b>Срок:</b> {deadline_str}"
        )

        # Используем существующую функцию send_telegram_message для отправки в общий чат
        from .telegram import send_telegram_message
        send_telegram_message(admin_message)
        print(f"   ✅ Уведомление отправлено в общий чат")
    except Exception as e:
        print(f"   ❌ Ошибка отправки в общий чат: {e}")

    print(f"{'=' * 60}\n")
    return result

def notify_homework_checked(homework, submission=None):
    """
    Отправляет уведомление ученику о проверке домашнего задания
    Может вызываться двумя способами:
    1. notify_homework_checked(homework) - без submission (берет последнюю сдачу)
    2. notify_homework_checked(homework, submission) - с конкретной сдачей
    """
    print(f"\n{'=' * 60}")
    print(f"🔔 ФУНКЦИЯ notify_homework_checked ВЫЗВАНА для ДЗ #{homework.id}")
    print(f"   Задание: {homework.title}")
    print(f"   Ученик: {homework.student.user.get_full_name()}")
    
    # Если submission не передан, пытаемся получить последнюю сдачу
    if submission is None:
        try:
            # Пытаемся получить последнюю сдачу через related_name 'submissions'
            if hasattr(homework, 'submissions') and homework.submissions.exists():
                submission = homework.submissions.latest('submitted_at')
                print(f"   ✅ Автоматически получена последняя сдача от {submission.submitted_at}")
            else:
                print(f"   ⚠️ Нет сданных работ для этого ДЗ")
                return False
        except Exception as e:
            print(f"   ⚠️ Ошибка при получении последней сдачи: {e}")
            return False
    
    print(f"   Оценка: {submission.grade if submission.grade else 'не указана'}")
    print(f"{'=' * 60}")

    notifier = TelegramNotifier()

    if not notifier.is_configured():
        print(f"❌ Telegram bot не настроен")
        logger.warning("Telegram bot not configured")
        return False

    student = homework.student
    teacher = homework.teacher

    # Проверяем, включены ли уведомления у ученика
    if not student.user.telegram_notifications or not student.user.telegram_chat_id:
        print(f"⚠️ У ученика {student.user.username} не включены Telegram уведомления или нет chat_id")
        return False

    # Формируем сообщение для ученика
    grade_text = f"{submission.grade}/5" if submission.grade else "не указана"
    grade_emoji = "🏆" if submission.grade == 5 else "⭐" if submission.grade and submission.grade >= 4 else "📝"
    
    message = (
        f"{grade_emoji} <b>Домашнее задание проверено!</b>\n\n"
        f"<b>Предмет:</b> {homework.subject.name}\n"
        f"<b>Учитель:</b> {teacher.user.get_full_name()}\n"
        f"<b>Название:</b> {homework.title}\n" 
        f"<b>Оценка:</b> {grade_text}\n"
    )
    
    if submission.teacher_comment:
        message += f"<b>Комментарий:</b> {submission.teacher_comment}\n"
    
    # Добавляем ссылку, если есть BASE_URL
    base_url = getattr(settings, 'BASE_URL', None)
    if base_url:
        message += f"\n🔗 <a href='{base_url}/student/homework/{homework.id}/'>Посмотреть результат</a>"

    # Отправляем сообщение ученику
    result = notifier.send_message_sync(student.user.telegram_chat_id, message)
    print(f"   Результат отправки ученику: {'✅ УСПЕШНО' if result else '❌ ОШИБКА'}")

    # Отправляем в общий админский чат
    try:
        admin_message = (
            f"✅ <b>Домашнее задание проверено</b>\n\n"
            f"👨‍🎓 <b>Ученик:</b> {student.user.get_full_name()}\n"
            f"👨‍🏫 <b>Учитель:</b> {teacher.user.get_full_name()}\n"
            f"📚 <b>Предмет:</b> {homework.subject.name}\n"
            f"📝 <b>Задание:</b> {homework.title}\n"
            f"⭐ <b>Оценка:</b> {grade_text}"
        )
        # Используем функцию для отправки в общий чат
        send_telegram_message(admin_message)
        print(f"   ✅ Уведомление отправлено в общий чат")
    except Exception as e:
        print(f"   ❌ Ошибка отправки в общий чат: {e}")

    print(f"{'=' * 60}\n")
    return result