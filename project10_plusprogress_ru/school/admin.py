
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.contrib.auth.models import User as AuthUser
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
    list_display = ('id', 'subject', 'teacher', 'student', 'date', 'start_time', 'status', 'cost')
    list_filter = ('status', 'subject', 'date', 'teacher', 'student')
    search_fields = ('teacher__user__last_name', 'student__user__last_name', 'subject__name')
    date_hierarchy = 'date'
    raw_id_fields = ('teacher', 'student')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('teacher', 'student', 'subject', 'format')
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
    list_display = ('teacher', 'get_day_display', 'start_time', 'end_time', 'is_active')
    list_filter = ('day_of_week', 'is_active', 'teacher')
    search_fields = ('teacher__user__last_name',)
    
    def get_day_display(self, obj):
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        return days[obj.day_of_week]
    get_day_display.short_description = 'День недели'


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