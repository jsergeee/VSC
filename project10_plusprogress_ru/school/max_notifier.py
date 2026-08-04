# school/max_notifier.py

import logging
from django.conf import settings
from .bot_service import MaxBotService

logger = logging.getLogger(__name__)


class MaxNotifier:
    """Класс для отправки уведомлений в MAX"""

    def __init__(self):
        self.bot_service = MaxBotService()

    def is_configured(self):
        """Проверяет, настроен ли бот"""
        return getattr(settings, 'MAX_BOT_TOKEN', None) is not None

    def send_message_to_user(self, user, message):
        """
        Отправляет сообщение пользователю в MAX
        """
        if not self.is_configured():
            logger.warning("MAX bot not configured")
            return False

        if not user.max_chat_id:
            logger.warning(f"У пользователя {user.username} нет max_chat_id")
            return False

        if not user.max_notifications:
            logger.info(f"У пользователя {user.username} отключены MAX уведомления")
            return False

        try:
            result = self.bot_service.send_message(
                chat_id=user.max_chat_id,
                message=message
            )
            if result and result.status == 'sent':
                logger.info(f"MAX сообщение отправлено пользователю {user.username}")
                return True
            else:
                logger.error(f"Ошибка отправки MAX сообщения пользователю {user.username}")
                return False
        except Exception as e:
            logger.error(f"Ошибка отправки MAX сообщения пользователю {user.username}: {e}")
            return False

    def send_message_to_admin(self, message):
        """
        Отправляет сообщение в общий админский чат MAX
        """
        if not self.is_configured():
            logger.warning("MAX bot not configured")
            return False

        admin_chat_id = getattr(settings, 'MAX_BOT_ADMIN_CHAT_ID', None)
        if not admin_chat_id:
            logger.warning("MAX_BOT_ADMIN_CHAT_ID not configured")
            return False

        try:
            result = self.bot_service.send_message(
                chat_id=admin_chat_id,
                message=message
            )
            if result and result.status == 'sent':
                logger.info(f"MAX сообщение отправлено в общий чат")
                return True
            else:
                logger.error("Ошибка отправки MAX сообщения в общий чат")
                return False
        except Exception as e:
            logger.error(f"Ошибка отправки MAX сообщения в общий чат: {e}")
            return False


# ===== ФУНКЦИИ ДЛЯ УВЕДОМЛЕНИЙ О РАЗНЫХ СОБЫТИЯХ =====

def notify_new_lesson_max(lesson):
    """
    Уведомление о новом уроке в MAX
    """
    notifier = MaxNotifier()

    if not notifier.is_configured():
        logger.warning("MAX bot not configured, пропускаем уведомление")
        return False

    students = lesson.students.all()
    students_names = ', '.join([s.user.get_full_name() for s in students])

    # Сообщение в общий админский чат
    admin_message = (
        f"📚 <b>Новый урок!</b>\n\n"
        f"👨‍🏫 Учитель: {lesson.teacher.user.get_full_name()}\n"
        f"👨‍🎓 Ученики: {students_names}\n"
        f"📅 Дата: {lesson.date}\n"
        f"⏰ Время: {lesson.start_time}\n"
        f"📖 Предмет: {lesson.subject.name}"
    )
    notifier.send_message_to_admin(admin_message)

    # Отправляем учителю
    teacher = lesson.teacher.user
    if teacher.max_chat_id and teacher.max_notifications:
        teacher_message = (
            f"📚 <b>У вас новый урок!</b>\n\n"
            f"👨‍🎓 Ученики: {students_names}\n"
            f"📅 Дата: {lesson.date}\n"
            f"⏰ Время: {lesson.start_time}\n"
            f"📖 Предмет: {lesson.subject.name}"
        )
        notifier.send_message_to_user(teacher, teacher_message)

    # Отправляем ученикам
    for student in students:
        if student.user.max_chat_id and student.user.max_notifications:
            student_message = (
                f"📚 <b>У вас новый урок!</b>\n\n"
                f"👨‍🏫 Учитель: {lesson.teacher.user.get_full_name()}\n"
                f"📅 Дата: {lesson.date}\n"
                f"⏰ Время: {lesson.start_time}\n"
                f"📖 Предмет: {lesson.subject.name}"
            )
            notifier.send_message_to_user(student.user, student_message)

    return True


def notify_lesson_completed_max(lesson, report=None):
    """
    Уведомление о завершении урока в MAX
    """
    notifier = MaxNotifier()

    if not notifier.is_configured():
        return False

    # Список учеников
    students_list = []
    total_cost = 0
    teacher_payment = 0

    for attendance in lesson.attendance.filter(status='attended'):
        student = attendance.student
        students_list.append(f"{student.user.get_full_name()} ({attendance.cost}₽)")
        total_cost += attendance.cost
        teacher_payment += attendance.teacher_payment_share

    students_text = ', '.join(students_list) if students_list else 'нет учеников'

    # Сообщение в общий чат
    admin_message = (
        f"✅ <b>УРОК ЗАВЕРШЕН!</b>\n\n"
        f"👨‍🏫 Учитель: {lesson.teacher.user.get_full_name()}\n"
        f"👨‍🎓 Ученики: {students_text}\n"
        f"📅 Дата: {lesson.date.strftime('%d.%m.%Y')}\n"
        f"⏰ Время: {lesson.start_time.strftime('%H:%M')} - {lesson.end_time.strftime('%H:%M')}\n"
        f"📖 Предмет: {lesson.subject.name}\n\n"
        f"💰 <b>ФИНАНСЫ:</b>\n"
        f"   • Оплачено учениками: {total_cost} ₽\n"
        f"   • Выплата учителю: {teacher_payment} ₽\n"
        f"   • Комиссия школы: {total_cost - teacher_payment} ₽\n"
    )
    if report and report.topic:
        admin_message += f"\n📝 Тема: {report.topic}"
    if report and report.homework:
        admin_message += f"\n📚 Домашнее задание: {report.homework[:100]}..."

    notifier.send_message_to_admin(admin_message)

    # Отправляем учителю
    teacher = lesson.teacher.user
    if teacher.max_chat_id and teacher.max_notifications:
        teacher_message = (
            f"✅ <b>Ваш урок завершен!</b>\n\n"
            f"👨‍🎓 Ученики: {students_text}\n"
            f"📅 Дата: {lesson.date.strftime('%d.%m.%Y')}\n"
            f"⏰ Время: {lesson.start_time.strftime('%H:%M')} - {lesson.end_time.strftime('%H:%M')}\n"
            f"📖 Предмет: {lesson.subject.name}\n\n"
            f"💰 <b>ВАША ВЫПЛАТА:</b> {teacher_payment} ₽\n"
        )
        if report and report.topic:
            teacher_message += f"\n📝 Тема: {report.topic}"
        notifier.send_message_to_user(teacher, teacher_message)

    # Отправляем ученикам
    for attendance in lesson.attendance.filter(status='attended'):
        student = attendance.student.user
        if student.max_chat_id and student.max_notifications:
            student_message = (
                f"✅ <b>Урок завершен!</b>\n\n"
                f"👨‍🏫 Учитель: {lesson.teacher.user.get_full_name()}\n"
                f"📅 Дата: {lesson.date.strftime('%d.%m.%Y')}\n"
                f"⏰ Время: {lesson.start_time.strftime('%H:%M')} - {lesson.end_time.strftime('%H:%M')}\n"
                f"📖 Предмет: {lesson.subject.name}\n\n"
                f"💰 Списано с баланса: {attendance.cost} ₽\n"
            )
            if report and report.topic:
                student_message += f"\n📝 Тема: {report.topic}"
            if report and report.homework:
                student_message += f"\n📚 Домашнее задание: {report.homework}"
            notifier.send_message_to_user(student, student_message)

    return True


def notify_new_homework_max(homework):
    """
    Уведомление о новом домашнем задании в MAX
    """
    notifier = MaxNotifier()

    if not notifier.is_configured():
        return False

    student = homework.student
    teacher = homework.teacher

    # Сообщение в общий чат
    admin_message = (
        f"📝 <b>Новое домашнее задание</b>\n\n"
        f"👨‍🎓 <b>Ученик:</b> {student.user.get_full_name()}\n"
        f"👨‍🏫 <b>Учитель:</b> {teacher.user.get_full_name()}\n"
        f"📚 <b>Предмет:</b> {homework.subject.name}\n"
        f"📝 <b>Задание:</b> {homework.title}\n"
        f"⏰ <b>Срок:</b> {homework.deadline.strftime('%d.%m.%Y %H:%M')}"
    )
    notifier.send_message_to_admin(admin_message)

    # Отправляем ученику
    if student.user.max_chat_id and student.user.max_notifications:
        student_message = (
            f"📝 <b>Новое домашнее задание</b>\n\n"
            f"<b>Предмет:</b> {homework.subject.name}\n"
            f"<b>Учитель:</b> {teacher.user.get_full_name()}\n"
            f"<b>Название:</b> {homework.title}\n"
            f"<b>Описание:</b> {homework.description[:200]}{'...' if len(homework.description) > 200 else ''}\n"
            f"<b>Срок сдачи:</b> {homework.deadline.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"🔗 Перейдите в ЛК для выполнения задания"
        )
        notifier.send_message_to_user(student.user, student_message)

    # Отправляем учителю
    if teacher.user.max_chat_id and teacher.user.max_notifications:
        teacher_message = (
            f"✅ <b>Домашнее задание создано</b>\n\n"
            f"<b>Ученик:</b> {student.user.get_full_name()}\n"
            f"<b>Предмет:</b> {homework.subject.name}\n"
            f"<b>Название:</b> {homework.title}"
        )
        notifier.send_message_to_user(teacher.user, teacher_message)

    return True


def notify_homework_checked_max(homework, submission=None):
    """
    Уведомление о проверке домашнего задания в MAX
    """
    notifier = MaxNotifier()

    if not notifier.is_configured():
        return False

    student = homework.student
    teacher = homework.teacher

    grade_text = f"{submission.grade}/5" if submission and submission.grade else "не указана"

    # Сообщение в общий чат
    admin_message = (
        f"✅ <b>Домашнее задание проверено</b>\n\n"
        f"👨‍🎓 <b>Ученик:</b> {student.user.get_full_name()}\n"
        f"👨‍🏫 <b>Учитель:</b> {teacher.user.get_full_name()}\n"
        f"📚 <b>Предмет:</b> {homework.subject.name}\n"
        f"📝 <b>Задание:</b> {homework.title}\n"
        f"⭐ <b>Оценка:</b> {grade_text}"
    )
    notifier.send_message_to_admin(admin_message)

    # Отправляем ученику
    if student.user.max_chat_id and student.user.max_notifications:
        message = (
            f"✅ <b>Домашнее задание проверено!</b>\n\n"
            f"<b>Предмет:</b> {homework.subject.name}\n"
            f"<b>Учитель:</b> {teacher.user.get_full_name()}\n"
            f"<b>Название:</b> {homework.title}\n"
            f"<b>Оценка:</b> {grade_text}\n"
        )
        if submission and submission.teacher_comment:
            message += f"<b>Комментарий:</b> {submission.teacher_comment}\n"
        message += f"\n🔗 Перейдите в ЛК для просмотра"
        notifier.send_message_to_user(student.user, message)

    return True


def notify_trial_request_max(trial_request):
    """
    Уведомление о новой заявке на пробный урок в MAX
    """
    notifier = MaxNotifier()

    if not notifier.is_configured():
        return False

    message = (
        f"📝 <b>Новая заявка на пробный урок!</b>\n\n"
        f"👤 Имя: {trial_request.name}\n"
        f"📧 Email: {trial_request.email or 'Не указан'}\n"
        f"📱 Телефон: {trial_request.phone}\n"
        f"📚 Предмет: {trial_request.subject}\n"
        f"🌐 IP: {trial_request.ip_address or 'Неизвестен'}"
    )

    return notifier.send_message_to_admin(message)


def notify_payment_max(user, amount, payment_type):
    """
    Уведомление о платеже в MAX
    """
    notifier = MaxNotifier()

    if not notifier.is_configured():
        return False

    emoji = '💰' if payment_type == 'income' else '💸'
    type_text = 'пополнение' if payment_type == 'income' else 'списание'

    # Сообщение в общий чат
    admin_message = (
        f"{emoji} <b>{type_text.title()}!</b>\n\n"
        f"👤 Пользователь: {user.get_full_name()}\n"
        f"💵 Сумма: {amount} ₽\n"
        f"📊 Текущий баланс: {user.get_balance()} ₽"
    )
    notifier.send_message_to_admin(admin_message)

    # Отправляем пользователю
    if user.max_chat_id and user.max_notifications:
        user_message = (
            f"{emoji} <b>{type_text.title()}!</b>\n\n"
            f"💵 Сумма: {amount} ₽\n"
            f"📊 Ваш текущий баланс: {user.get_balance()} ₽"
        )
        notifier.send_message_to_user(user, user_message)

    return True