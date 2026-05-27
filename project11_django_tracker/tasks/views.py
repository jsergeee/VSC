from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import Task

@login_required
def task_list(request):
    """Список задач текущего пользователя"""
    tasks = Task.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'tasks/list.html', {'tasks': tasks})

@login_required
def task_create(request):
    """Создание задачи"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        if title:
            Task.objects.create(
                user=request.user,
                title=title,
                description=description
            )
            return redirect('tasks:task_list')
    return render(request, 'tasks/create.html')

@login_required
def task_update_status(request, pk):
    """Обновление статуса задачи"""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    status = request.GET.get('status')
    if status in dict(Task.STATUS_CHOICES):
        task.status = status
        task.save()
    return redirect('tasks:task_list')

@login_required
def task_delete(request, pk):
    """Удаление задачи"""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.delete()
    return redirect('tasks:task_list')