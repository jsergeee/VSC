from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Lesson, Notification, User, LessonAttendance, Payment, LessonReport
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Lesson
from .telegram import notify_new_lesson


@receiver(post_save, sender=LessonAttendance)
def attendance_created(sender, instance, created, **kwargs):
    """Создает уведомление когда ученик добавлен к уроку"""
    if created:
        print("=" * 50)
        print(f"✅ Ученик добавлен к уроку {instance.lesson.id}")
        print(f"   Ученик: {instance.student.user.get_full_name()}")

        lesson = instance.lesson

        # Уведомление ученику
        Notification.objects.create(
            user=instance.student.user,
            title='📚 Новое занятие',
            message=f'Запланировано занятие по {lesson.subject.name} с {lesson.teacher.user.get_full_name()} на {lesson.date.strftime("%d.%m.%Y")} в {lesson.start_time.strftime("%H:%M")}',
            notification_type='lesson_reminder',
            link=f'/student/lesson/{lesson.id}/'
        )
        print(f"✅ Уведомление ученику создано")

        # Проверяем, нужно ли отправить уведомление учителю (первый ученик)
        if lesson.attendance.count() == 1:
            Notification.objects.create(
                user=lesson.teacher.user,
                title='📚 Новое занятие',
                message=f'Запланировано занятие по {lesson.subject.name} с учеником {instance.student.user.get_full_name()} на {lesson.date.strftime("%d.%m.%Y")} в {lesson.start_time.strftime("%H:%M")}',
                notification_type='lesson_reminder',
                link=f'/teacher/lesson/{lesson.id}/'
            )
            print(f"✅ Уведомление учителю создано")
        print("=" * 50)


@receiver(post_save, sender=User)
def send_welcome_notification(sender, instance, created, **kwargs):
    """Приветственное уведомление для новых пользователей"""
    if created:
        Notification.objects.create(
            user=instance,
            title='👋 Добро пожаловать!',
            message='Рады видеть вас в школе "Плюс Прогресс"',
            notification_type='system',
            expires_at=timezone.now() + timedelta(days=30)
        )
        print(f"✅ Приветственное уведомление для {instance.username}")


# ============================================
# 🔥 НОВЫЙ СИГНАЛ: Уведомления при завершении урока
# ============================================
@receiver(post_save, sender=LessonReport)
def lesson_completed_notifications(sender, instance, created, **kwargs):
    """
    Сигнал для создания уведомлений при завершении урока
    """
    if created:
        lesson = instance.lesson

        print("\n" + "🔥" * 60)
        print("🔥 ЭКСТРЕННАЯ ДИАГНОСТИКА")
        print(f"🔥 Урок ID: {lesson.id}")
        print(f"🔥 Статус урока: {lesson.status}")

        # 1. Прямой SQL запрос в обход Django ORM
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, student_id, status, teacher_payment_share 
                FROM school_lessonattendance 
                WHERE lesson_id = %s
            """, [lesson.id])
            rows = cursor.fetchall()

            print(f"\n📊 ПРЯМОЙ SQL ЗАПРОС:")
            for row in rows:
                print(f"   ID: {row[0]}, Student: {row[1]}, Status: {row[2]}, Payment: {row[3]}")

        # 2. Проверка через ORM
        print(f"\n📊 ORM ЗАПРОС:")
        all_att = lesson.attendance.all()
        print(f"   Всего записей: {all_att.count()}")

        attended_ids = []
        for a in all_att:
            print(f"   - {a.student.user.get_full_name()}: статус={a.status}, payment={a.teacher_payment_share}")
            if a.status == 'attended':
                attended_ids.append(a.id)

        # 3. Принудительное обновление из БД
        print(f"\n📊 ПОСЛЕ refresh_from_db():")
        lesson.refresh_from_db()
        for a in lesson.attendance.all():
            print(f"   - {a.student.user.get_full_name()}: статус={a.status}")

        # 4. Расчет выплаты
        teacher_payment = 0
        if attended_ids:
            attended = lesson.attendance.filter(id__in=attended_ids)
            teacher_payment = sum(float(a.teacher_payment_share) for a in attended)

        print(f"\n💰 ИТОГО: присутствовало {len(attended_ids)}, выплата {teacher_payment}")
        print("🔥" * 60 + "\n")

        # Создаем уведомления только если есть присутствовавшие
        if attended_ids:
            # Уведомление учителю
            try:
                Notification.objects.create(
                    user=lesson.teacher.user,
                    title='✅ Занятие проведено',
                    message=f'Урок "{lesson.subject.name}" от {lesson.date} завершен. Присутствовало: {len(attended_ids)} учеников. Выплата: {teacher_payment:.0f} ₽',
                    notification_type='lesson_completed',
                )
            except Exception as e:
                print(f"❌ Ошибка: {e}")

            # Уведомления ученикам
            for attendance in attended:
                try:
                    Notification.objects.create(
                        user=attendance.student.user,
                        title='✅ Занятие проведено',
                        message=f'Урок "{lesson.subject.name}" от {lesson.date} завершен. Отчет доступен в дневнике.',
                        notification_type='lesson_completed',
                    )
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
        else:
            print("⚠️ Нет присутствовавших - уведомления не созданы")
            
            
  # добавьте в начало файла, если нет

@receiver(post_delete, sender=Payment)
def delete_payment_notifications(sender, instance, **kwargs):
    """
    Удаляет все уведомления, связанные с платежом, при его удалении
    """
    print(f"\n{'💰' * 30}")
    print(f"💰 Сигнал: удаление платежа #{instance.id}")
    print(f"   Пользователь: {instance.user.username}")
    print(f"   Сумма: {instance.amount}")
    print(f"   Тип: {instance.payment_type}")
    
    # Находим все уведомления, связанные с этим платежом
    notifications = Notification.objects.filter(payment=instance)
    
    count = notifications.count()
    if count > 0:
        # Удаляем все связанные уведомления
        notifications.delete()
        print(f"   ✅ Удалено уведомлений: {count}")
        
        # Дополнительно: ищем уведомления по тексту (на всякий случай)
        text_notifications = Notification.objects.filter(
            user=instance.user,
            message__icontains=f"{instance.amount} ₽"
        )
        text_count = text_notifications.count()
        if text_count > 0:
            text_notifications.delete()
            print(f"   ✅ Дополнительно удалено по тексту: {text_count}")
    else:
        print(f"   ⚠️ Связанных уведомлений не найдено")
    
    print(f"{'💰' * 30}\n")

    @receiver(post_save, sender=Lesson)
    def lesson_created_notification(sender, instance, created, **kwargs):
        """
        Отправляет уведомление при создании нового урока
        """
        if created:
            notify_new_lesson(instance)