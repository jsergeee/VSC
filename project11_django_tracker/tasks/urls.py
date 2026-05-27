from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('create/', views.task_create, name='task_create'),
    path('<int:pk>/update-status/', views.task_update_status, name='task_update_status'),
    path('<int:pk>/delete/', views.task_delete, name='task_delete'),
]