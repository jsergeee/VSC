
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.contrib.auth.models import User as AuthUser
from django.urls import path
from django.shortcuts import render
from .views import schedule_calendar_data
from .views import schedule_calendar_data, admin_complete_lesson
from django.contrib import messages
from .models import (
    User, Subject, Teacher, Student, Lesson, LessonFormat,
    LessonReport, Payment, Schedule, TrialRequest
)
try:
    admin.site.unregister(AuthUser)
except admin.sites.NotRegistered:
    pass

class CustomUserAdmin(UserAdmin):
    # Отображаемые поля в списке пользователей
    list_display = ('username', 'get_full_name', 'email', 'phone', 'role', 'balance', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    
    # Поля для редактирования при изменении пользователя
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личная информация', {
            'fields': ('first_name', 'last_name', 'patronymic', 'email', 'phone', 'photo')
        }),
        ('Роль и баланс', {
            'fields': ('role', 'balance'),
            'classes': ('wide',),
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Поля, которые будут отображаться при создании нового пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 
                      'first_name', 'last_name', 'patronymic', 
                      'email', 'phone', 'role'),
        }),
    )
    
    def get_full_name(self, obj):
        full_name = obj.get_full_name()
        if obj.patronymic:
            return f"{full_name} {obj.patronymic}"
        return full_name or obj.username
    get_full_name.short_description = 'ФИО'
    get_full_name.admin_order_field = 'last_name'


# Добавляем класс SubjectAdmin
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_subjects', 'experience', 'wallet_balance', 'created')
    list_filter = ('subjects',)
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    
    def display_subjects(self, obj):
        return ", ".join([s.name for s in obj.subjects.all()])
    display_subjects.short_description = 'Предметы'
    
    def created(self, obj):
        return obj.user.date_joined.strftime('%d.%m.%Y')
    created.short_description = 'Дата регистрации'


class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'parent_name', 'parent_phone', 'get_teachers_count')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'parent_name')
    filter_horizontal = ('teachers',)
    list_filter = ('teachers',)
    raw_id_fields = ('user',)
    
    def get_teachers_count(self, obj):
        return obj.teachers.count()
    get_teachers_count.short_description = 'Кол-во учителей'


# Добавляем класс LessonFormatAdmin
class LessonFormatAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'teacher', 'student', 'date', 'start_time', 'status', 'cost', 'has_report')
    list_filter = ('status', 'subject', 'date', 'teacher', 'student')
    search_fields = ('teacher__user__last_name', 'student__user__last_name', 'subject__name')
    date_hierarchy = 'date'
    raw_id_fields = ('teacher', 'student')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('teacher', 'student', 'subject', 'format', 'schedule')
        }),
        ('Время', {
            'fields': ('date', 'start_time', 'end_time', 'duration')
        }),
        ('Финансы', {
            'fields': ('cost', 'teacher_payment')
        }),
        ('Платформа', {
            'fields': ('meeting_link', 'meeting_platform')
        }),
        ('Статус', {
            'fields': ('status', 'notes')
        }),
    )
    
    readonly_fields = ('duration', 'created_at', 'updated_at')
    
    def has_report(self, obj):
        from django.utils.html import format_html
        if hasattr(obj, 'report'):
            url = f'/admin/school/lessonreport/{obj.report.id}/change/'
            return format_html('<a href="{}" style="color: #28a745;">✅ Отчет #{}</a>', url, obj.report.id)
        return '❌ Нет отчета'
    has_report.short_description = 'Отчет'
    
    def save_model(self, request, obj, form, change):
        """Переопределяем сохранение модели"""
        old_status = None
        if change:  # Если редактируем существующий объект
            try:
                old_obj = self.model.objects.get(pk=obj.pk)
                old_status = old_obj.status
            except:
                pass
        
        super().save_model(request, obj, form, change)
        
        # Если статус изменился на 'completed' и нет отчета
        if obj.status == 'completed' and not hasattr(obj, 'report'):
            # Создаем автоматический отчет
            from .models import LessonReport
            report = LessonReport.objects.create(
                lesson=obj,
                topic=f'Занятие по {obj.subject.name}',
                covered_material='Материал был пройден на занятии',
                homework='Домашнее задание',
                student_progress='Прогресс отмечен',
                next_lesson_plan='Продолжение темы'
            )
            
            # Начисляем выплату учителю
            obj.teacher.wallet_balance += obj.teacher_payment
            obj.teacher.save()
            
            # Списание с баланса ученика
            if obj.student:
                obj.student.user.balance -= obj.cost
                obj.student.user.save()
                
                # Создаем запись о платеже
                from .models import Payment
                Payment.objects.create(
                    user=obj.student.user,
                    amount=obj.cost,
                    payment_type='expense',
                    description=f'Оплата занятия {obj.date} ({obj.subject.name})',
                    lesson=obj
                )
            
            self.message_user(request, f'✅ Автоматически создан отчет #{report.id}', level='SUCCESS')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:lesson_id>/complete/', 
                 self.admin_site.admin_view(admin_complete_lesson), 
                 name='complete-lesson'),
        ]
        return custom_urls + urls
    
    
    


class LessonReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'lesson_link', 'topic_preview', 'created_at', 'lesson_status', 'payment_info')
    list_filter = ('created_at', 'lesson__subject', 'lesson__teacher', 'lesson__status')
    search_fields = ('topic', 'lesson__subject__name', 'lesson__teacher__user__last_name')
    readonly_fields = ('created_at', 'lesson_details', 'payment_details')
    
    def lesson_link(self, obj):
        from django.utils.html import format_html
        url = f'/admin/school/lesson/{obj.lesson.id}/change/'
        return format_html('<a href="{}">{} #{}</a>', url, obj.lesson.subject, obj.lesson.id)
    lesson_link.short_description = 'Занятие'
    
    def topic_preview(self, obj):
        return obj.topic[:50] + '...' if len(obj.topic) > 50 else obj.topic
    topic_preview.short_description = 'Тема'
    
    def lesson_status(self, obj):
        status = obj.lesson.status
        colors = {
            'completed': '#28a745',
            'overdue': '#dc3545',
            'scheduled': '#ffc107',
            'cancelled': '#6c757d'
        }
        from django.utils.html import format_html
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(status, '#17a2b8'),
            obj.lesson.get_status_display()
        )
    lesson_status.short_description = 'Статус'
    
    def payment_info(self, obj):
        from django.utils.html import format_html
        return format_html('{} руб. / {} руб.', obj.lesson.cost, obj.lesson.teacher_payment)
    payment_info.short_description = 'Стоимость/Выплата'
    
    def lesson_details(self, obj):
        from django.utils.html import format_html
        return format_html('''
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                <p><strong>Предмет:</strong> {}</p>
                <p><strong>Учитель:</strong> {}</p>
                <p><strong>Ученик:</strong> {}</p>
                <p><strong>Дата:</strong> {} {} - {}</p>
                <p><strong>Стоимость:</strong> {} руб.</p>
                <p><strong>Выплата учителю:</strong> {} руб.</p>
            </div>
        ''',
            obj.lesson.subject.name,
            obj.lesson.teacher.user.get_full_name(),
            obj.lesson.student.user.get_full_name() if obj.lesson.student else 'Не назначен',
            obj.lesson.date,
            obj.lesson.start_time,
            obj.lesson.end_time,
            obj.lesson.cost,
            obj.lesson.teacher_payment
        )
    lesson_details.short_description = 'Детали занятия'
    
    def payment_details(self, obj):
        payments = obj.lesson.payment_set.all()
        if payments:
            from django.utils.html import format_html
            html = '<ul style="margin:0; padding-left:20px;">'
            for p in payments:
                html += f'<li>{p.get_payment_type_display()}: {p.amount} руб. ({p.created_at.date()})</li>'
            html += '</ul>'
            return format_html(html)
        return 'Нет платежей'
    payment_details.short_description = 'Платежи'
    
    fieldsets = (
        ('Информация о занятии', {
            'fields': ('lesson_details',)
        }),
        ('Содержание отчета', {
            'fields': ('topic', 'covered_material', 'homework', 'student_progress', 'next_lesson_plan')
        }),
        ('Финансовая информация', {
            'fields': ('payment_details',)
        }),
        ('Дата создания', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

class LessonReportAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'topic', 'created_at')
    search_fields = ('lesson__subject__name', 'topic')
    raw_id_fields = ('lesson',)


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_type', 'description', 'created_at')
    list_filter = ('payment_type', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'description')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'lesson')


class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'day_display', 'start_time', 'end_time', 'is_active')
    list_filter = ('day_of_week', 'is_active', 'teacher')
    search_fields = ('teacher__user__last_name',)
    
    def day_display(self, obj):
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        return days[obj.day_of_week]
    day_display.short_description = 'День недели'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('calendar-data/', self.admin_site.admin_view(schedule_calendar_data), name='schedule-calendar-data'),
        ]
        return custom_urls + urls
    
def changelist_view(self, request, extra_context=None):
    from datetime import date
    from .models import Lesson
    
    extra_context = extra_context or {}
    extra_context['total_schedules'] = Schedule.objects.count()
    extra_context['active_schedules'] = Schedule.objects.filter(is_active=True).count()
    
    # Статистика по занятиям
    extra_context['total_lessons'] = Lesson.objects.count()
    extra_context['completed_lessons'] = Lesson.objects.filter(status='completed').count()
    extra_context['scheduled_lessons'] = Lesson.objects.filter(status='scheduled').count()
    extra_context['overdue_lessons'] = Lesson.objects.filter(status='overdue').count()
    
    return super().changelist_view(request, extra_context)

class TrialRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'subject', 'created_at', 'is_processed')
    list_filter = ('is_processed', 'subject', 'created_at')
    search_fields = ('name', 'phone', 'email')
    date_hierarchy = 'created_at'


# Register your models here
admin.site.register(User, CustomUserAdmin)
admin.site.register(Subject, SubjectAdmin)  # Теперь SubjectAdmin определен
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(LessonFormat, LessonFormatAdmin)  # Добавляем LessonFormatAdmin
admin.site.register(Lesson, LessonAdmin)
admin.site.register(LessonReport, LessonReportAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(TrialRequest, TrialRequestAdmin)

# Настройка заголовка админ-панели
admin.site.site_header = 'Администрирование Плюс Прогресс'
admin.site.site_title = 'Плюс Прогресс'
admin.site.index_title = 'Управление онлайн школой'
# school/admin.py