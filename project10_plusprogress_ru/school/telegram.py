import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram_message(text, parse_mode='HTML'):
    """
    Отправляет сообщение в Telegram
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
        logger.info(f"Telegram сообщение отправлено: {text[:50]}...")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка отправки в Telegram: {e}")
        return False


def notify_new_lesson(lesson):
    """Уведомление о новом уроке"""
    text = f"""
<b>📚 Новый урок!</b>

👨‍🏫 Учитель: {lesson.teacher.user.get_full_name()}
👨‍🎓 Ученики: {', '.join([s.user.get_full_name() for s in lesson.students.all()])}
📅 Дата: {lesson.date}
⏰ Время: {lesson.start_time}
📖 Предмет: {lesson.subject.name}
"""
    send_telegram_message(text)


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

    text = f"""
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
        text += f"\n📚 Домашнее задание: {report.homework[:100]}..."

    text += f"\n\n🔗 Ссылка на отчет: http://127.0.0.1:8000/admin/school/lessonreport/{report.id if report else ''}/change/"

    send_telegram_message(text)

def notify_payment(user, amount, payment_type):
    """Уведомление о платеже"""
    emoji = '💰' if payment_type == 'income' else '💸'
    type_text = 'пополнение' if payment_type == 'income' else 'списание'

    text = f"""
{emoji} <b>{type_text.title()}!</b>

👤 Пользователь: {user.get_full_name()}
💵 Сумма: {amount} ₽
📊 Текущий баланс: {user.get_balance()} ₽
"""
    send_telegram_message(text)


def notify_homework_submitted(homework):
    """Уведомление о сданном ДЗ"""
    text = f"""
<b>📤 Сдано домашнее задание!</b>

👨‍🎓 Ученик: {homework.student.user.get_full_name()}
📚 Задание: {homework.title}
⏰ Сдано: {homework.submission.submitted_at.strftime('%d.%m.%Y %H:%M')}
"""
    send_telegram_message(text)