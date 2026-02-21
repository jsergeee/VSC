from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.contrib.auth.models import User as AuthUser
from django.urls import path
from django.shortcuts import render
from django import forms
from django.db import models
from django.utils import timezone

from .models import (
    User, Subject, Teacher, Student, Lesson, LessonFormat,
    LessonReport, Payment, Schedule, TrialRequest,
    Notification, LessonFeedback, TeacherRating,
    Homework, HomeworkSubmission
)
from .views import schedule_calendar_data, admin_complete_lesson

# Разрегистрируем стандартного User, если зарегистрирован
try:
    admin.site.unregister(AuthUser)
except admin.sites.NotRegistered:
    pass


# ==================== CUSTOM USER ADMIN ====================
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'email', 'phone', 'role', 'balance', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')

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


# ==================== SUBJECT ADMIN ====================
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


# ==================== TEACHER ADMIN ====================
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_subjects', 'experience', 'created')
    list_filter = ('subjects',)
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    filter_horizontal = ('subjects',)

    fieldsets = (
        (None, {
            'fields': ('user', 'subjects', 'experience')
        }),
        ('Дополнительная информация', {
            'fields': ('education', 'bio', 'wallet_balance', 'payment_details'),
            'classes': ('collapse',),
        }),
    )

    def display_subjects(self, obj):
        return ", ".join([s.name for s in obj.subjects.all()])

    display_subjects.short_description = 'Предметы'

    def created(self, obj):
        return obj.user.date_joined.strftime('%d.%m.%Y')

    created.short_description = 'Дата регистрации'


# ==================== STUDENT ADMIN ====================
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
        balance = obj.user.balance
        if balance > 0:
            return format_html('<span style="color: #28a745;">💰 {}</span>', f"{balance:.2f}")
        elif balance < 0:
            return format_html('<span style="color: #dc3545;">🔴 {}</span>', f"{balance:.2f}")
        return format_html('<span style="color: #6c757d;">⚪ 0.00</span>')

    get_balance_display.short_description = 'Баланс'


# ==================== LESSON FORMAT ADMIN ====================
class LessonFormatAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


# ==================== LESSON ADMIN ====================
class LessonAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TimeField: {'widget': forms.TimeInput(format='%H:%M', attrs={'type': 'time'})},
        models.DateField: {'widget': forms.DateInput(attrs={'type': 'date'})},
    }

    list_display = ('id', 'subject', 'teacher', 'student', 'date', 'start_time', 'status', 'cost', 'has_report')
    list_filter = ('status', 'subject', 'date', 'teacher', 'student')
    search_fields = ('teacher__user__last_name', 'student__user__last_name', 'subject__name')
    date_hierarchy = 'date'
    raw_id_fields = ('teacher', 'student')

    fieldsets = (
        ('Основная информация', {
            'fields': ('teacher', 'student', 'subject', 'format')
        }),
        ('Время', {
            'fields': ('date', 'start_time', 'end_time')
        }),
        ('Финансы', {
            'fields': ('cost', 'teacher_payment')
        }),
        ('Платформа', {
            'fields': ('meeting_link',)
        }),
        ('Статус', {
            'fields': ('status', 'notes')
        }),
    )

    def has_report(self, obj):
        if hasattr(obj, 'report'):
            url = f'/admin/school/lessonreport/{obj.report.id}/change/'
            return format_html('<a href="{}" style="color: #28a745;">✅ Отчет #{}</a>', url, obj.report.id)
        return '❌ Нет отчета'

    has_report.short_description = 'Отчет'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:lesson_id>/complete/',
                 self.admin_site.admin_view(admin_complete_lesson),
                 name='complete-lesson'),
        ]
        return custom_urls + urls


# ==================== LESSON REPORT ADMIN ====================
class LessonReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'lesson_link', 'topic_preview', 'created_at')
    list_filter = ('created_at', 'lesson__subject')
    search_fields = ('topic', 'lesson__subject__name')
    readonly_fields = ('created_at',)
    raw_id_fields = ('lesson',)

    def lesson_link(self, obj):
        url = f'/admin/school/lesson/{obj.lesson.id}/change/'
        return format_html('<a href="{}">{} #{}</a>', url, obj.lesson.subject, obj.lesson.id)

    lesson_link.short_description = 'Занятие'

    def topic_preview(self, obj):
        return obj.topic[:50] + '...' if len(obj.topic) > 50 else obj.topic

    topic_preview.short_description = 'Тема'


# ==================== PAYMENT ADMIN ====================
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_type', 'description', 'created_at')
    list_filter = ('payment_type', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'description')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'lesson')


# ==================== SCHEDULE ADMIN ====================
class ScheduleAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TimeField: {'widget': forms.TimeInput(format='%H:%M', attrs={'type': 'time'})},
        models.DateField: {'widget': forms.DateInput(attrs={'type': 'date'})},
    }

    list_display = ('teacher', 'date', 'day_of_week_display', 'start_time', 'end_time', 'is_active')
    list_filter = ('date', 'is_active', 'teacher')
    search_fields = ('teacher__user__last_name',)

    def day_of_week_display(self, obj):
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        return days[obj.date.weekday()]

    day_of_week_display.short_description = 'День'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('calendar-data/', self.admin_site.admin_view(schedule_calendar_data), name='schedule-calendar-data'),
        ]
        return custom_urls + urls


# ==================== TRIAL REQUEST ADMIN ====================
class TrialRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'subject', 'created_at', 'is_processed')
    list_filter = ('is_processed', 'subject', 'created_at')
    search_fields = ('name', 'phone', 'email')
    date_hierarchy = 'created_at'


# ==================== NOTIFICATION ADMIN ====================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'user__email', 'title')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user',)
    list_per_page = 50


# ==================== LESSON FEEDBACK ADMIN ====================
@admin.register(LessonFeedback)
class LessonFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'lesson', 'student', 'teacher', 'rating_stars', 'created_at', 'is_public')
    list_filter = ('rating', 'is_public', 'created_at')
    search_fields = ('student__user__last_name', 'teacher__user__last_name', 'comment')
    raw_id_fields = ('lesson', 'student', 'teacher')
    date_hierarchy = 'created_at'
    actions = ['make_public', 'make_private']

    def rating_stars(self, obj):
        return '⭐' * obj.rating

    rating_stars.short_description = 'Оценка'

    def make_public(self, request, queryset):
        queryset.update(is_public=True)
        self.message_user(request, f'✅ {queryset.count()} оценок опубликовано')

    make_public.short_description = 'Опубликовать'

    def make_private(self, request, queryset):
        queryset.update(is_public=False)
        self.message_user(request, f'🔒 {queryset.count()} оценок скрыто')

    make_private.short_description = 'Скрыть'


# ==================== TEACHER RATING ADMIN ====================
@admin.register(TeacherRating)
class TeacherRatingAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'average_rating_display', 'total_feedbacks', 'updated_at')
    list_select_related = ('teacher__user',)
    readonly_fields = ('teacher', 'average_rating', 'total_feedbacks', 'rating_5_count',
                       'rating_4_count', 'rating_3_count', 'rating_2_count', 'rating_1_count', 'updated_at')

    def average_rating_display(self, obj):
        return f"{obj.average_rating:.1f} ⭐"

    average_rating_display.short_description = 'Средний балл'


# ==================== HOMEWORK ADMIN ====================
@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('id', 'colored_title', 'student_name', 'teacher_name', 'subject',
                    'colored_deadline', 'colored_status')
    list_filter = ('subject', 'is_active', 'deadline')
    search_fields = ('title', 'student__user__last_name', 'teacher__user__last_name')
    date_hierarchy = 'deadline'
    raw_id_fields = ('student', 'teacher', 'subject')
    list_per_page = 25
    save_on_top = True

    def student_name(self, obj):
        return obj.student.user.get_full_name()

    student_name.short_description = 'Ученик'

    def teacher_name(self, obj):
        return obj.teacher.user.get_full_name()

    teacher_name.short_description = 'Учитель'

    def colored_title(self, obj):
        return format_html('<span style="color: #2c3e50; font-weight: bold;">{}</span>', obj.title)

    colored_title.short_description = 'Название'

    def colored_deadline(self, obj):
        now = timezone.now()
        if obj.deadline < now:
            return format_html('<span style="color: #dc3545;">⚠️ {}</span>',
                               obj.deadline.strftime('%d.%m.%Y %H:%M'))
        elif (obj.deadline - now).days < 1:
            return format_html('<span style="color: #ffc107;">⚡ {}</span>',
                               obj.deadline.strftime('%d.%m.%Y %H:%M'))
        else:
            return format_html('<span style="color: #28a745;">✅ {}</span>',
                               obj.deadline.strftime('%d.%m.%Y %H:%M'))

    colored_deadline.short_description = 'Срок сдачи'

    def colored_status(self, obj):
        status = obj.get_status()
        colors = {
            'pending': ('#ffc107', '⏳ Ожидает'),
            'submitted': ('#17a2b8', '📤 На проверке'),
            'checked': ('#28a745', '✅ Проверено'),
            'overdue': ('#dc3545', '⚠️ Просрочено'),
        }
        color, text = colors.get(status, ('#6c757d', '❓'))
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, text)

    colored_status.short_description = 'Статус'


# ==================== HOMEWORK SUBMISSION ADMIN ====================
@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'homework_link', 'student_name', 'submitted_at', 'status_colored', 'grade_display')
    list_filter = ('status', 'submitted_at')
    search_fields = ('homework__title', 'student__user__last_name')
    date_hierarchy = 'submitted_at'

    def homework_link(self, obj):
        url = f'/admin/school/homework/{obj.homework.id}/change/'
        return format_html('<a href="{}">{}</a>', url, obj.homework.title)

    homework_link.short_description = 'Задание'

    def student_name(self, obj):
        return obj.student.user.get_full_name()

    student_name.short_description = 'Ученик'

    def status_colored(self, obj):
        if obj.status == 'submitted':
            return format_html('<span style="color: #17a2b8;">📤 Ожидает проверки</span>')
        return format_html('<span style="color: #28a745;">✅ Проверено</span>')

    status_colored.short_description = 'Статус'

    def grade_display(self, obj):
        if obj.grade:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 3px;">{}/5</span>',
                obj.grade)
        return '—'

    grade_display.short_description = 'Оценка'


# ==================== REGISTER ALL MODELS ====================
admin.site.register(User, CustomUserAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(LessonFormat, LessonFormatAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(LessonReport, LessonReportAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(TrialRequest, TrialRequestAdmin)

# Настройка заголовков админки
admin.site.site_header = 'Плюс Прогресс - Администрирование'
admin.site.site_title = 'Плюс Прогресс'
admin.site.index_title = 'Управление онлайн школой'