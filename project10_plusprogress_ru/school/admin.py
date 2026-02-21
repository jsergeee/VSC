
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.contrib.auth.models import User as AuthUser
from django.urls import path
from django.shortcuts import render
from .views import schedule_calendar_data
from .views import schedule_calendar_data, admin_complete_lesson
from django.contrib import messages
from django import forms
from django.db import models
from .models import Schedule, Lesson
from .views import schedule_calendar_data
from .models import Notification
from .models import LessonFeedback, TeacherRating
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
    list_display = ('user', 'display_subjects', 'experience', 'created')
    list_filter = ('subjects',)
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    
    # Явно указываем все поля, которые должны быть в карточке
    fieldsets = (
        (None, {
            'fields': ('user', 'subjects', 'experience')
        }),
        ('Дополнительная информация', {
            'fields': ('education', 'bio'),  # Только существующие поля
            'classes': ('collapse',),
        }),
    )
      # Добавляем filter_horizontal для поля subjects
    filter_horizontal = ('subjects',)
    
    def display_subjects(self, obj):
        return ", ".join([s.name for s in obj.subjects.all()])
    display_subjects.short_description = 'Предметы'
    
    def created(self, obj):
        return obj.user.date_joined.strftime('%d.%m.%Y')
    created.short_description = 'Дата регистрации'
    
    def display_subjects(self, obj):
        return ", ".join([s.name for s in obj.subjects.all()])
    display_subjects.short_description = 'Предметы'
    
    def created(self, obj):
        return obj.user.date_joined.strftime('%d.%m.%Y')
    created.short_description = 'Дата регистрации'


class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'parent_name', 'parent_phone', 'get_teachers_count', 'get_balance_display')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'parent_name')
    filter_horizontal = ('teachers',)
    list_filter = ('teachers',)
    raw_id_fields = ('user',)
    
    def get_teachers_count(self, obj):
        return obj.teachers.count()
    get_teachers_count.short_description = 'Кол-во учителей'
    
    def get_balance_display(self, obj):
        """Отображает баланс ученика с цветовой индикацией"""
        balance = obj.user.balance
        formatted_balance = f"{balance:,.2f}".replace(',', ' ').replace('.', ',')
        
        # Выбираем цвет и иконку в зависимости от баланса
        if balance > 0:
            color = '#28a745'  # зеленый
            icon = '💰'
        elif balance < 0:
            color = '#dc3545'  # красный
            icon = '🔴'
        else:
            color = '#6c757d'  # серый
            icon = '⚪'
        
        from django.utils.html import format_html
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            formatted_balance
        )
    get_balance_display.short_description = 'Баланс'
    get_balance_display.admin_order_field = 'user__balance'


# Добавляем класс LessonFormatAdmin
class LessonFormatAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
class LessonAdmin(admin.ModelAdmin):
    # Кастомные виджеты для времени и даты
    formfield_overrides = {
        models.TimeField: {'widget': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'vTimeField'})},
        models.DateField: {'widget': forms.DateInput(attrs={'type': 'date', 'class': 'vDateField'})},
    }
    
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
    
    def changelist_view(self, request, extra_context=None):
        # Если запрошен календарь
        if request.GET.get('view') == 'calendar':
            lessons = self.get_queryset(request).select_related(
                'teacher__user', 'student__user', 'subject'
            )
            extra_context = extra_context or {}
            extra_context['lessons'] = lessons
            extra_context['title'] = 'Календарь занятий'
            
            return render(request, 'admin/school/lesson/change_list_calendar.html', extra_context)
        
        # Обычный список
        return super().changelist_view(request, extra_context)
    
    
    


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
        # Кастомная форма с виджетами
    formfield_overrides = {
        models.TimeField: {'widget': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'vTimeField'})},
        models.DateField: {'widget': forms.DateInput(attrs={'type': 'date', 'class': 'vDateField'})},
    }
    
    list_display = ('teacher', 'date', 'day_of_week_display', 'start_time', 'end_time', 'is_active')
    list_filter = ('date', 'is_active', 'teacher')
    search_fields = ('teacher__user__last_name',)
    
    fieldsets = (
        (None, {
            'fields': ('teacher', 'date', 'start_time', 'end_time', 'is_active')
        }),
    )
    
    def day_of_week_display(self, obj):
        """Отображает день недели на основе даты"""
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        return days[obj.date.weekday()]
    day_of_week_display.short_description = 'День недели'
    
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
        extra_context['lessons_today'] = Lesson.objects.filter(date=date.today()).count()
        
        return super().changelist_view(request, extra_context)

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




@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'user__email', 'title']
    date_hierarchy = 'created_at'
    raw_id_fields = ['user']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    

@admin.register(LessonFeedback)
class LessonFeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'lesson', 'student', 'teacher', 'rating_stars', 'created_at', 'is_public']
    list_filter = ['rating', 'is_public', 'created_at']
    search_fields = ['student__user__last_name', 'teacher__user__last_name', 'comment']
    raw_id_fields = ['lesson', 'student', 'teacher']
    date_hierarchy = 'created_at'
    actions = ['make_public', 'make_private']
    
    def rating_stars(self, obj):
        return '⭐' * obj.rating
    rating_stars.short_description = 'Оценка'
    
    def make_public(self, request, queryset):
        queryset.update(is_public=True)
        self.message_user(request, f'Отмечено {queryset.count()} оценок как публичные')
    make_public.short_description = 'Сделать публичными'
    
    def make_private(self, request, queryset):
        queryset.update(is_public=False)
        self.message_user(request, f'Отмечено {queryset.count()} оценок как приватные')
    make_private.short_description = 'Сделать приватными'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Обновляем рейтинг учителя
        rating, created = TeacherRating.objects.get_or_create(teacher=obj.teacher)
        rating.update_stats()


@admin.register(TeacherRating)
class TeacherRatingAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'average_rating_display', 'total_feedbacks', 'rating_distribution', 'updated_at']
    list_select_related = ['teacher__user']
    readonly_fields = ['teacher', 'average_rating', 'total_feedbacks', 'rating_5_count', 'rating_4_count', 'rating_3_count', 'rating_2_count', 'rating_1_count', 'updated_at']
    
    def average_rating_display(self, obj):
        return f"{obj.average_rating:.1f} ⭐"
    average_rating_display.short_description = 'Средний балл'
    
    def rating_distribution(self, obj):
        if obj.total_feedbacks == 0:
            return 'Нет оценок'
        return f"5⭐:{obj.rating_5_count} 4⭐:{obj.rating_4_count} 3⭐:{obj.rating_3_count} 2⭐:{obj.rating_2_count} 1⭐:{obj.rating_1_count}"
    rating_distribution.short_description = 'Распределение'