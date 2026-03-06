from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('teachers', views.TeacherViewSet)
router.register('students', views.StudentViewSet)
router.register('lessons', views.LessonViewSet)
router.register('homeworks', views.HomeworkViewSet)
router.register('submissions', views.HomeworkSubmissionViewSet)
router.register('materials', views.MaterialViewSet)
router.register('payments', views.PaymentViewSet)
router.register('feedbacks', views.LessonFeedbackViewSet)
router.register('group-lessons', views.GroupLessonViewSet)
router.register('group-enrollments', views.GroupEnrollmentViewSet)
router.register('schedule-templates', views.ScheduleTemplateViewSet)
router.register('student-prices', views.StudentSubjectPriceViewSet)
router.register('trial-requests', views.TrialRequestViewSet)
router.register('deposits', views.DepositViewSet)
router.register('student-notes', views.StudentNoteViewSet)
router.register('payment-requests', views.PaymentRequestViewSet)
router.register('lesson-reports', views.LessonReportViewSet),
router.register('notifications', views.NotificationViewSet, basename='notification')


urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='api-register'),
    path('', include(router.urls)),
    path('login/', views.LoginAPIView.as_view(), name='api-login'),
    
]