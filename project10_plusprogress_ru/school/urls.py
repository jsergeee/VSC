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
    
    # Student URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/calendar/', views.student_calendar, name='student_calendar'),
    
    # Teacher URLs
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    
    # Lesson URLs
    path('lessons/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    
    path('api/schedules/', views.api_schedules, name='api_schedules'),
    
    path('reports/overdue/', views.overdue_report, name='overdue_report'),
    
    path('admin/school/schedule/calendar-data/', views.schedule_calendar_data, name='schedule-calendar-data'),
    
    path('admin/school/lesson/<int:lesson_id>/complete/', views.admin_complete_lesson, name='admin-complete-lesson'),
    
        # Student URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/materials/', views.student_materials, name='student_materials'),
    path('student/deposit/', views.student_deposit, name='student_deposit'),
    
    # Teacher URLs
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/student/<int:student_id>/', views.teacher_student_detail, name='teacher_student_detail'),
    path('teacher/materials/', views.teacher_materials, name='teacher_materials'),
]