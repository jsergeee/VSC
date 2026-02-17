# school/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    User, Teacher, Student, Lesson, Subject, 
    LessonReport, Payment, TrialRequest, Schedule
)
from .forms import (
    UserRegistrationForm, UserLoginForm, TrialRequestForm,
    LessonReportForm, ProfileUpdateForm
)


def home(request):
    trial_form = TrialRequestForm()
    if request.method == 'POST':
        trial_form = TrialRequestForm(request.POST)
        if trial_form.is_valid():
            trial_form.save()
            messages.success(request, 'Заявка успешно отправлена! Мы свяжемся с вами в ближайшее время.')
            return redirect('home')
    
    context = {
        'trial_form': trial_form,
        'subjects': Subject.objects.all(),
    }
    return render(request, 'school/home.html', context)


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'school/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Неверное имя пользователя или пароль')
    else:
        form = UserLoginForm()
    return render(request, 'school/login.html', {'form': form})


@login_required
def user_logout(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    user = request.user
    
    if user.role == 'student':
        return redirect('student_dashboard')
    elif user.role == 'teacher':
        return redirect('teacher_dashboard')
    else:
        return redirect('admin_dashboard')


@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    
    student = request.user.student_profile
    today = timezone.now().date()
    
    # Получаем расписание
    upcoming_lessons = Lesson.objects.filter(
        student=student,
        date__gte=today,
        status='scheduled'
    ).order_by('date', 'start_time')[:10]
    
    # История занятий
    past_lessons = Lesson.objects.filter(
        student=student,
        status='completed'
    ).order_by('-date', '-start_time')[:10]
    
    # Баланс
    balance = request.user.balance
    
    # Последние платежи
    recent_payments = Payment.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'student': student,
        'upcoming_lessons': upcoming_lessons,
        'past_lessons': past_lessons,
        'balance': balance,
        'recent_payments': recent_payments,
    }
    return render(request, 'school/student/dashboard.html', context)


@login_required
def student_calendar(request):
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    
    student = request.user.student_profile
    
    # Получаем все занятия ученика
    lessons = Lesson.objects.filter(student=student).order_by('date', 'start_time')
    
    # Преобразуем в формат для календаря
    calendar_events = []
    for lesson in lessons:
        calendar_events.append({
            'title': f"{lesson.subject.name} - {lesson.teacher.user.get_full_name()}",
            'start': f"{lesson.date}T{lesson.start_time}",
            'end': f"{lesson.date}T{lesson.end_time}",
            'url': f"/lessons/{lesson.id}/",
            'status': lesson.status,
        })
    
    context = {
        'calendar_events': calendar_events,
    }
    return render(request, 'school/student/calendar.html', context)


@login_required
def teacher_dashboard(request):
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    
    teacher = request.user.teacher_profile
    today = timezone.now().date()
    
    # Список учеников
    students = Student.objects.filter(teachers=teacher)
    
    # Расписание на сегодня
    today_lessons = Lesson.objects.filter(
        teacher=teacher,
        date=today
    ).order_by('start_time')
    
    # Предстоящие занятия
    upcoming_lessons = Lesson.objects.filter(
        teacher=teacher,
        date__gt=today,
        status='scheduled'
    ).order_by('date', 'start_time')[:10]
    
    # Баланс кошелька
    wallet_balance = teacher.wallet_balance
    
    # Недавние выплаты
    recent_payments = Payment.objects.filter(
        user=request.user,
        payment_type='teacher_payment'
    ).order_by('-created_at')[:5]
    
    context = {
        'teacher': teacher,
        'students': students,
        'today_lessons': today_lessons,
        'upcoming_lessons': upcoming_lessons,
        'wallet_balance': wallet_balance,
        'recent_payments': recent_payments,
    }
    return render(request, 'school/teacher/dashboard.html', context)


@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    # Проверка доступа
    user = request.user
    if user.role == 'student' and lesson.student.user != user:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    elif user.role == 'teacher' and lesson.teacher.user != user:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    
    report = None
    if hasattr(lesson, 'report'):
        report = lesson.report
    
    if request.method == 'POST' and user.role == 'teacher':
        form = LessonReportForm(request.POST, instance=report)
        if form.is_valid():
            report = form.save(commit=False)
            report.lesson = lesson
            report.save()
            
            # Обновляем статус урока
            lesson.status = 'completed'
            lesson.save()
            
            messages.success(request, 'Отчет сохранен')
            return redirect('lesson_detail', lesson_id=lesson.id)
    else:
        form = LessonReportForm(instance=report)
    
    context = {
        'lesson': lesson,
        'report': report,
        'form': form if user.role == 'teacher' and lesson.status != 'completed' else None,
    }
    return render(request, 'school/lesson_detail.html', context)


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлен')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'school/profile.html', {'form': form})