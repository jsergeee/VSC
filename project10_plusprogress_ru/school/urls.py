# school/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),

    # Email verification
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),

    # Student URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),

    # Teacher URLs
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('admin/school/teacher/<int:teacher_id>/report/', views.teacher_report, name='admin-teacher-report'),
    path('admin/teacher-payments/', views.teacher_payments_dashboard, name='teacher-payments-dashboard'),
    path('admin/teacher-payments/calculate/', views.calculate_teacher_payment, name='calculate-teacher-payment'),
    path('admin/teacher-payments/export/<str:format>/<int:teacher_id>/<str:start_date>/<str:end_date>/',
         views.export_teacher_payment, name='export-teacher-payment'),

    # Lesson URLs
    path('lessons/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('api/schedules/', views.api_schedules, name='api_schedules'),
    path('reports/overdue/', views.overdue_report, name='overdue_report'),
    path('admin/school/schedule/calendar-data/', views.schedule_calendar_data, name='schedule-calendar-data'),
    path('admin/school/lesson/<int:lesson_id>/complete/', views.admin_complete_lesson, name='admin-complete-lesson'),
    path('admin/school/lesson/export/<str:format>/', views.admin_lesson_export, name='admin-lesson-export'),
    path('admin/school/lesson/import/', views.import_lessons, name='admin-lesson-import'),
    path('admin/school/lesson/import/template/', views.download_import_template, name='admin-lesson-import-template'),
    # АДМИН
    path('admin/finance/dashboard/', views.admin_finance_dashboard, name='admin-finance-dashboard'),
    # Student URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/materials/', views.student_materials, name='student_materials'),
    path('student/deposit/', views.student_deposit, name='student_deposit'),
    path('admin/school/student/<int:student_id>/report/', views.student_report, name='admin-student-report'),
    path('lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('lesson/<int:lesson_id>/feedback/', views.lesson_feedback, name='lesson_feedback'),


    # Teacher URLs
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/student/<int:student_id>/', views.teacher_student_detail, name='teacher_student_detail'),
    path('teacher/materials/', views.teacher_materials, name='teacher_materials'),
    path('teacher/lesson/<int:lesson_id>/', views.teacher_lesson_detail, name='teacher_lesson_detail'),
    path('lesson/<int:lesson_id>/complete/', views.complete_lesson, name='complete_lesson'),
    path('api/lesson/<int:lesson_id>/create-video-room/', views.create_video_room, name='create_video_room'),
    path('teacher/schedule-templates/', views.teacher_schedule_templates, name='teacher_schedule_templates'),
    path('teacher/schedule-template/create/', views.teacher_schedule_template_create,
         name='teacher_schedule_template_create'),
    path('teacher/schedule-template/<int:template_id>/', views.teacher_schedule_template_detail,
         name='teacher_schedule_template_detail'),
    path('teacher/lesson/<int:lesson_id>/edit/', views.teacher_edit_lesson, name='teacher_edit_lesson'),
    path('teacher/group-lessons/', views.teacher_group_lessons, name='teacher_group_lessons'),
    path('teacher/group-lesson/<int:lesson_id>/', views.teacher_group_lesson_detail,
         name='teacher_group_lesson_detail'),
    path('teacher/group-lessons/', views.teacher_group_lessons, name='teacher_group_lessons'),
    path('teacher/group-lesson/<int:lesson_id>/', views.teacher_group_lesson_detail,
         name='teacher_group_lesson_detail'),
    path('teacher/group-lesson/<int:lesson_id>/attendance/', views.mark_group_attendance, name='mark_group_attendance'),
    path('teacher/group-lesson/<int:lesson_id>/complete/', views.complete_group_lesson, name='complete_group_lesson'),
    path('teacher/schedule-template/<int:template_id>/delete/', views.teacher_schedule_template_delete,
         name='teacher_schedule_template_delete'),
    path('teacher/schedule/create/', views.teacher_create_schedule, name='teacher_create_schedule'),

    # Уведомления
    path('api/notifications/', views.get_notifications, name='api_notifications'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    # Оценки уроков
    path('lesson/<int:lesson_id>/feedback/', views.lesson_feedback, name='lesson_feedback'),
    path('teacher/feedbacks/', views.teacher_feedbacks, name='teacher_feedbacks'),
    path('student/feedbacks/', views.student_feedbacks, name='student_feedbacks'),

    # Домашние задания
    path('teacher/homeworks/', views.teacher_homeworks, name='teacher_homeworks'),
    path('teacher/homework/create/<int:student_id>/', views.teacher_homework_create, name='teacher_homework_create'),
    path('teacher/homework/<int:homework_id>/', views.teacher_homework_detail, name='teacher_homework_detail'),

    path('student/homeworks/', views.student_homeworks, name='student_homeworks'),
    path('student/homework/<int:homework_id>/', views.student_homework_detail, name='student_homework_detail'),

    # Импорты
    path('admin/school/student/import/', views.import_students, name='import-students'),
    path('admin/school/student/download-template/', views.download_student_template, name='download-student-template'),
    path('admin/school/teacher/import/', views.import_teachers, name='import-teachers'),
    path('admin/school/teacher/download-template/', views.download_teacher_template, name='download-teacher-template'),
    
        # URL для скачивания шаблона импорта пользователей
    path('admin/user/download-template/', views.download_user_template, name='download_user_template'),
    path('admin/user/import/', views.import_users_view, name='import_users'),
]
