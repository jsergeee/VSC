# school/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from datetime import datetime, date, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from django.contrib import messages
from django.db.models import Q, Sum
from datetime import date, timedelta
from .models import Student, Teacher, Lesson, Material, Deposit, StudentNote
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
    """Личный кабинет ученика"""
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    
    # ПОЛНОЕ обновление пользователя из базы данных
    # Это гарантирует, что мы видим актуальные данные
    user = User.objects.get(pk=request.user.pk)
    
    from .models import Student, Lesson, Material
    from datetime import date
    from django.db.models import Q
    
    # Получаем профиль ученика
    try:
        student = user.student_profile
    except:
        student = Student.objects.create(user=user)
        messages.info(request, 'Профиль ученика был создан')
    
    # Принудительно обновляем профиль из базы
    student.refresh_from_db()
    
    # Получаем баланс
    balance = student.get_balance()
    
    # Получаем учителей ученика (свежие данные)
    teachers = student.teachers.all()
    
    # Получаем ближайшие занятия
    upcoming_lessons = Lesson.objects.filter(
        student=student,
        date__gte=date.today(),
        status='scheduled'
    ).select_related('teacher__user', 'subject', 'format').order_by('date', 'start_time')[:10]
    
    # Получаем последние проведенные занятия
    past_lessons = Lesson.objects.filter(
        student=student,
        status='completed'
    ).select_related('teacher__user', 'subject').order_by('-date')[:10]
    
    # Получаем методические материалы
    materials = Material.objects.filter(
        Q(students=student) | Q(is_public=True) | Q(teachers__in=teachers)
    ).distinct()[:20]
    
    # Отладка - выведем в консоль, что получаем
    import logging
    logging.info(f"Student: {student}")
    logging.info(f"Teachers count: {teachers.count()}")
    logging.info(f"Upcoming lessons: {upcoming_lessons.count()}")
    
    context = {
        'student': student,
        'balance': balance,
        'upcoming_lessons': upcoming_lessons,
        'past_lessons': past_lessons,
        'teachers': teachers,
        'materials': materials,
        'debug_user': user.username,
        'debug_student_id': student.id,
    }
    
    return render(request, 'school/student/dashboard_new.html', context)

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

@require_GET
def api_schedules(request):
    """API для календаря расписаний"""
    schedules = Schedule.objects.filter(is_active=True).select_related('teacher__user')
    
    events = []
    today = date.today()
    
    for schedule in schedules:
        # Генерируем события на месяц вперед
        for i in range(30):
            event_date = today + timedelta(days=i)
            if event_date.weekday() == schedule.day_of_week:
                # Проверяем, есть ли занятие в это время
                lesson = Lesson.objects.filter(
                    teacher=schedule.teacher,
                    date=event_date,
                    start_time=schedule.start_time
                ).first()
                
                start_dt = datetime.combine(event_date, schedule.start_time)
                end_dt = datetime.combine(event_date, schedule.end_time)
                
                event = {
                    'id': f"schedule_{schedule.id}_{event_date}",
                    'teacher_name': schedule.teacher.user.get_full_name(),
                    'subject': 'Расписание',
                    'start': start_dt.isoformat(),
                    'end': end_dt.isoformat(),
                    'color': '#28a745' if lesson else '#3788d8',
                }
                
                if lesson:
                    event['subject'] = lesson.subject.name
                    event['student_name'] = lesson.student.user.get_full_name()
                    event['status'] = lesson.status
                
                events.append(event)
    
    return JsonResponse(events, safe=False)

@login_required
def overdue_report(request):
    """Отчет по просроченным занятиям"""
    if request.user.role not in ['admin', 'teacher']:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    
    # Обновляем статусы просроченных занятий
    now = timezone.now()
    overdue_lessons = Lesson.objects.filter(
        status='scheduled',
        date__lt=now.date()
    ) | Lesson.objects.filter(
        status='scheduled',
        date=now.date(),
        start_time__lt=now.time()
    )
    
    for lesson in overdue_lessons:
        lesson.check_overdue()
    
    # Фильтры
    teacher_id = request.GET.get('teacher')
    student_id = request.GET.get('student')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    lessons = Lesson.objects.filter(status='overdue').select_related(
        'teacher__user', 'student__user', 'subject'
    )
    
    if teacher_id:
        lessons = lessons.filter(teacher_id=teacher_id)
    if student_id:
        lessons = lessons.filter(student_id=student_id)
    if date_from:
        lessons = lessons.filter(date__gte=date_from)
    if date_to:
        lessons = lessons.filter(date__lte=date_to)
    
    # Статистика
    stats = {
        'total': lessons.count(),
        'by_teacher': lessons.values('teacher__user__last_name').annotate(
            count=Count('id')
        ).order_by('-count'),
        'by_subject': lessons.values('subject__name').annotate(
            count=Count('id')
        ).order_by('-count'),
    }
    
    context = {
        'lessons': lessons.order_by('-date', '-start_time'),
        'stats': stats,
        'teachers': Teacher.objects.all(),
        'students': Student.objects.all(),
    }
    
    return render(request, 'school/reports/overdue.html', context)

@staff_member_required
def schedule_calendar_data(request):
    """API для календаря расписаний"""
    schedules = Schedule.objects.filter(is_active=True).select_related('teacher__user')
    
    events = []
    today = date.today()
    
    for i in range(60):
        event_date = today + timedelta(days=i)
        
        # Ищем расписания на эту дату
        day_schedules = schedules.filter(date=event_date)
        
        for schedule in day_schedules:
            # Ищем занятие на это время
            lesson = Lesson.objects.filter(
                teacher=schedule.teacher,
                date=event_date,
                start_time=schedule.start_time
            ).first()
            
            start_dt = datetime.combine(event_date, schedule.start_time)
            end_dt = datetime.combine(event_date, schedule.end_time)
            
            # Определяем цвет
            color = '#79aec8'  # синий по умолчанию (свободно)
            if lesson:
                if lesson.status == 'completed':
                    color = '#28a745'  # зеленый
                elif lesson.status == 'overdue':
                    color = '#dc3545'  # красный
                elif lesson.status == 'scheduled':
                    color = '#007bff'  # синий
                elif lesson.status == 'cancelled':
                    color = '#fd7e14'  # оранжевый
            
            event = {
                'id': f"schedule_{schedule.id}_{event_date}",
                'schedule_id': schedule.id,
                'teacher_name': schedule.teacher.user.get_full_name(),
                'start': start_dt.isoformat(),
                'end': end_dt.isoformat(),
                'color': color,
            }
            
            if lesson:
                event['lesson_id'] = lesson.id
                event['title'] = f"{schedule.teacher.user.last_name} - {lesson.subject.name}"
                if lesson.student:
                    event['title'] += f" ({lesson.student.user.last_name})"
            else:
                event['title'] = f"{schedule.teacher.user.last_name} - свободно"
            
            events.append(event)
    
    return JsonResponse(events, safe=False)

@staff_member_required
@require_POST
def admin_complete_lesson(request, lesson_id):
    """Завершает занятие из админ-панели"""
    try:
        lesson = Lesson.objects.get(pk=lesson_id)
        
        if lesson.status == 'completed':
            return JsonResponse({'success': False, 'error': 'Занятие уже завершено'})
        
        report_data = {
            'topic': request.POST.get('topic'),
            'covered_material': request.POST.get('covered_material'),
            'homework': request.POST.get('homework'),
            'student_progress': request.POST.get('student_progress'),
            'next_lesson_plan': request.POST.get('next_lesson_plan', '')
        }
        
        # Проверяем обязательные поля
        if not all([report_data['topic'], report_data['covered_material'], 
                   report_data['homework'], report_data['student_progress']]):
            return JsonResponse({'success': False, 'error': 'Заполните все обязательные поля'})
        
        report = lesson.mark_as_completed(report_data)
        
        return JsonResponse({
            'success': True,
            'report_id': report.id,
            'message': f'Занятие завершено. Создан отчет #{report.id}'
        })
        
    except Lesson.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Занятие не найдено'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def student_dashboard(request):
    """Личный кабинет ученика"""
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    
    student = request.user.student_profile
    
    # Получаем баланс
    balance = student.get_balance()
    
    # Получаем последние депозиты
    recent_deposits = student.deposits.all()[:5]
    
    # Получаем ближайшие занятия
    upcoming_lessons = Lesson.objects.filter(
        student=student,
        date__gte=date.today(),
        status='scheduled'
    ).select_related('teacher__user', 'subject', 'format').order_by('date', 'start_time')[:10]
    
    # Получаем учителей ученика
    teachers = student.teachers.all()
    
    # Получаем методические материалы (для этого ученика или публичные)
    materials = Material.objects.filter(
        Q(students=student) | Q(is_public=True) | Q(teachers__in=teachers)
    ).distinct()[:20]
    
    # Получаем последние проведенные занятия
    past_lessons = Lesson.objects.filter(
        student=student,
        status='completed'
    ).select_related('teacher__user', 'subject').order_by('-date')[:10]
    
    context = {
        'student': student,
        'balance': balance,
        'recent_deposits': recent_deposits,
        'upcoming_lessons': upcoming_lessons,
        'past_lessons': past_lessons,
        'teachers': teachers,
        'materials': materials,
    }
    
    return render(request, 'school/student/dashboard_new.html', context)


@login_required
def student_materials(request):
    """Все методические материалы для ученика"""
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    
    student = request.user.student_profile
    teachers = student.teachers.all()
    
    materials = Material.objects.filter(
        Q(students=student) | Q(is_public=True) | Q(teachers__in=teachers)
    ).distinct().order_by('-created_at')
    
    # Фильтр по предметам
    subject_id = request.GET.get('subject')
    if subject_id:
        materials = materials.filter(subjects__id=subject_id)
    
    # Фильтр по типу
    material_type = request.GET.get('type')
    if material_type:
        materials = materials.filter(material_type=material_type)
    
    subjects = Subject.objects.all()
    
    context = {
        'materials': materials,
        'subjects': subjects,
        'student': student,
    }
    
    return render(request, 'school/student/materials.html', context)


@login_required
def teacher_dashboard(request):
    """Личный кабинет учителя"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    
    teacher = request.user.teacher_profile
    
    # Получаем всех учеников учителя
    students = teacher.student_set.all().select_related('user')
    
    # Получаем ближайшие занятия
    upcoming_lessons = Lesson.objects.filter(
        teacher=teacher,
        date__gte=date.today(),
        status='scheduled'
    ).select_related('student__user', 'subject').order_by('date', 'start_time')[:20]
    
    # Получаем занятия на сегодня
    today_lessons = Lesson.objects.filter(
        teacher=teacher,
        date=date.today(),
        status='scheduled'
    ).select_related('student__user', 'subject').order_by('start_time')
    
    # Получаем методические материалы учителя
    materials = Material.objects.filter(
        Q(teachers=teacher) | Q(created_by=request.user)
    ).distinct().order_by('-created_at')[:20]
    
    # Баланс кошелька
    wallet_balance = teacher.wallet_balance
    
    # Недавние выплаты
    recent_payments = Payment.objects.filter(
        user=request.user,
        payment_type='teacher_payment'
    ).order_by('-created_at')[:10]
    
    context = {
        'teacher': teacher,
        'students': students,
        'upcoming_lessons': upcoming_lessons,
        'today_lessons': today_lessons,
        'materials': materials,
        'wallet_balance': wallet_balance,
        'recent_payments': recent_payments,
    }
    
    return render(request, 'school/teacher/dashboard_new.html', context)


@login_required
def teacher_student_detail(request, student_id):
    """Детальная информация об ученике для учителя"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    
    teacher = request.user.teacher_profile
    student = get_object_or_404(Student, id=student_id, teachers=teacher)
    
    # Получаем занятия с этим учеником
    lessons = Lesson.objects.filter(
        teacher=teacher,
        student=student
    ).select_related('subject', 'format').order_by('-date')
    
    # Получаем заметки учителя об этом ученике
    notes = StudentNote.objects.filter(teacher=teacher, student=student).order_by('-created_at')
    
    # Получаем материалы, доступные ученику
    materials = Material.objects.filter(
        Q(students=student) | Q(is_public=True)
    ).distinct()
    
    # Статистика
    total_lessons = lessons.count()
    completed_lessons = lessons.filter(status='completed').count()
    total_cost = lessons.filter(status='completed').aggregate(Sum('cost'))['cost__sum'] or 0
    
    context = {
        'student': student,
        'lessons': lessons[:20],
        'notes': notes,
        'materials': materials,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'total_cost': total_cost,
    }
    
    return render(request, 'school/teacher/student_detail.html', context)


@login_required
def teacher_materials(request):
    """Управление методическими материалами для учителя"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    
    teacher = request.user.teacher_profile
    materials = Material.objects.filter(
        Q(teachers=teacher) | Q(created_by=request.user)
    ).distinct().order_by('-created_at')
    
    # Фильтр по ученикам
    student_id = request.GET.get('student')
    if student_id:
        materials = materials.filter(students__id=student_id)
    
    students = teacher.student_set.all()
    
    context = {
        'materials': materials,
        'students': students,
        'teacher': teacher,
    }
    
    return render(request, 'school/teacher/materials.html', context)


@login_required
def student_deposit(request):
    """Пополнение баланса ученика"""
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        description = request.POST.get('description', 'Пополнение счета')
        
        try:
            amount = float(amount)
            if amount <= 0:
                messages.error(request, 'Сумма должна быть положительной')
                return redirect('student_dashboard')
            
            student = request.user.student_profile
            
            # Создаем депозит
            deposit = Deposit.objects.create(
                student=student,
                amount=amount,
                description=description,
                created_by=request.user
            )
            
            # Обновляем баланс пользователя
            request.user.balance += amount
            request.user.save()
            
            messages.success(request, f'Счет пополнен на {amount} ₽')
            
        except (ValueError, TypeError):
            messages.error(request, 'Неверная сумма')
        
        return redirect('student_dashboard')
    
    return redirect('student_dashboard')