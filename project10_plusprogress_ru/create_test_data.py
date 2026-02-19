# create_test_data.py
import os
import django
import random
from datetime import time, date, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plusprogress.settings')
django.setup()

from school.models import (
    User, Subject, Teacher, Student, Lesson, 
    LessonFormat, Schedule, Payment, Deposit
)

def create_test_data():
    print("=" * 60)
    print("СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ")
    print("=" * 60)
    
    # 1. ПРЕДМЕТЫ
    print("\n1. СОЗДАЕМ ПРЕДМЕТЫ:")
    subjects_list = [
        'Математика', 'Русский язык', 'Литература', 'Физика', 'Химия',
        'Биология', 'История', 'Обществознание', 'География', 'Английский язык',
        'Информатика', 'Алгебра', 'Геометрия'
    ]
    
    subjects = []
    for name in subjects_list:
        subject, created = Subject.objects.get_or_create(
            name=name,
            defaults={'description': f'Изучение {name.lower()}'}
        )
        subjects.append(subject)
        print(f"  {'[+]' if created else '[ ]'} {name}")
    
    # 2. ФОРМАТЫ ЗАНЯТИЙ
    print("\n2. СОЗДАЕМ ФОРМАТЫ ЗАНЯТИЙ:")
    formats_list = ['Zoom', 'Skype', 'Google Meet', 'Telegram', 'WhatsApp']
    
    formats = []
    for name in formats_list:
        fmt, created = LessonFormat.objects.get_or_create(
            name=name,
            defaults={'description': f'Платформа {name}'}
        )
        formats.append(fmt)
        print(f"  {'[+]' if created else '[ ]'} {name}")
    
    # 3. УЧИТЕЛЯ (10)
    print("\n3. СОЗДАЕМ УЧИТЕЛЕЙ:")
    
    teachers_data = [
        {'first': 'Гульмира', 'last': 'Яковенко', 'patr': 'Булатовна', 'subj': ['Английский язык']},
        {'first': 'Иван', 'last': 'Петров', 'patr': 'Иванович', 'subj': ['Математика', 'Алгебра', 'Геометрия']},
        {'first': 'Мария', 'last': 'Сидорова', 'patr': 'Алексеевна', 'subj': ['Русский язык', 'Литература']},
        {'first': 'Алексей', 'last': 'Смирнов', 'patr': 'Петрович', 'subj': ['Физика', 'Химия']},
        {'first': 'Елена', 'last': 'Козлова', 'patr': 'Дмитриевна', 'subj': ['Биология', 'История']},
        {'first': 'Дмитрий', 'last': 'Морозов', 'patr': 'Сергеевич', 'subj': ['Информатика', 'Математика']},
        {'first': 'Анна', 'last': 'Волкова', 'patr': 'Игоревна', 'subj': ['Английский язык', 'Обществознание']},
        {'first': 'Сергей', 'last': 'Федоров', 'patr': 'Андреевич', 'subj': ['География', 'Биология']},
        {'first': 'Ольга', 'last': 'Морозова', 'patr': 'Викторовна', 'subj': ['Химия', 'Физика']},
        {'first': 'Павел', 'last': 'Соколов', 'patr': 'Алексеевич', 'subj': ['История', 'Обществознание']},
    ]
    
    teachers = []
    for i, data in enumerate(teachers_data, 1):
        username = f"teacher_{i:02d}"
        email = f"{username}@school.ru"
        phone = f"+7901{i:06d}"
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': data['first'],
                'last_name': data['last'],
                'patronymic': data['patr'],
                'email': email,
                'phone': phone,
                'role': 'teacher',
                'balance': 0
            }
        )
        
        if created:
            user.set_password('password123')
            user.save()
            print(f"  [+] {user.get_full_name()}")
        else:
            print(f"  [ ] {user.get_full_name()} (уже существует)")
        
        teacher, _ = Teacher.objects.get_or_create(user=user)
        
        for subj_name in data['subj']:
            subject = Subject.objects.filter(name=subj_name).first()
            if subject:
                teacher.subjects.add(subject)
        
        teacher.experience = random.randint(3, 15)
        teacher.wallet_balance = 0
        teacher.save()
        teachers.append(teacher)
    
    # 4. УЧЕНИКИ (30)
    print("\n4. СОЗДАЕМ УЧЕНИКОВ:")
    
    first_names = [
        'Александр', 'Максим', 'Артем', 'Михаил', 'Даниил', 'Кирилл', 'Егор', 'Никита', 'Илья', 'Андрей',
        'Анастасия', 'Дарья', 'Мария', 'Екатерина', 'Виктория', 'Полина', 'София', 'Ксения', 'Алиса', 'Валерия',
        'Дмитрий', 'Сергей', 'Антон', 'Иван', 'Павел', 'Роман', 'Ольга', 'Татьяна', 'Наталья', 'Светлана'
    ]
    
    last_names = [
        'Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов', 'Попов', 'Васильев', 'Зайцев', 'Соколов', 'Михайлов',
        'Новикова', 'Федорова', 'Морозова', 'Волкова', 'Алексеева', 'Лебедева', 'Семенова', 'Егорова', 'Павлова', 'Козлова',
        'Николаев', 'Орлов', 'Макаров', 'Андреев', 'Ермаков', 'Ковалев', 'Ильина', 'Максимова', 'Соловьева', 'Тимофеева'
    ]
    
    students = []
    for i in range(30):
        username = f"student_{i+1:02d}"
        email = f"{username}@student.ru"
        phone = f"+7902{i+1:06d}"
        first = first_names[i]
        last = last_names[i]
        
        # Чередуем отчества
        if i % 3 == 0:
            patronymic = f"{first}ович" if first.endswith(('й', 'р')) else f"{first}евич"
        elif i % 3 == 1:
            patronymic = f"{first}овна" if first.endswith(('а', 'я')) else f"{first}евна"
        else:
            patronymic = ""
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first,
                'last_name': last,
                'patronymic': patronymic,
                'email': email,
                'phone': phone,
                'role': 'student',
                'balance': 0  # Начинаем с нулевым балансом
            }
        )
        
        if created:
            user.set_password('password123')
            user.save()
            print(f"  [+] {user.get_full_name()}")
        else:
            print(f"  [ ] {user.get_full_name()} (уже существует)")
        
        student, _ = Student.objects.get_or_create(user=user)
        
        # Добавляем 2-3 случайных учителя
        num_teachers = random.randint(2, 3)
        selected = random.sample(teachers, min(num_teachers, len(teachers)))
        student.teachers.set(selected)
        student.save()
        students.append(student)
    
    # 5. СОЗДАЕМ ЗАНЯТИЯ
    print("\n5. СОЗДАЕМ ЗАНЯТИЯ:")
    
    start_date = date(2026, 2, 10)
    end_date = date(2026, 3, 31)
    
    # Выходные и праздники
    holidays = [
        date(2026, 2, 14), date(2026, 2, 15),  # выходные
        date(2026, 2, 21), date(2026, 2, 22),  # выходные
        date(2026, 2, 23),  # праздник
        date(2026, 2, 28), date(2026, 3, 1),   # выходные
        date(2026, 3, 7), date(2026, 3, 8),    # выходные + праздник
        date(2026, 3, 14), date(2026, 3, 15),  # выходные
        date(2026, 3, 21), date(2026, 3, 22),  # выходные
        date(2026, 3, 28), date(2026, 3, 29),  # выходные
        date(2026, 3, 31),  # последний день
    ]
    
    # Временные слоты (с 9 до 20)
    time_slots = [
        (time(9, 0), time(10, 0)),
        (time(10, 0), time(11, 0)),
        (time(11, 0), time(12, 0)),
        (time(13, 0), time(14, 0)),
        (time(14, 0), time(15, 0)),
        (time(15, 0), time(16, 0)),
        (time(16, 0), time(17, 0)),
        (time(17, 0), time(18, 0)),
        (time(18, 0), time(19, 0)),
        (time(19, 0), time(20, 0)),
    ]
    
    lessons_created = 0
    target_lessons = 100
    
    # Определяем статусы для разных периодов
    first_period_end = date(2026, 2, 19)
    
    while lessons_created < target_lessons:
        # Выбираем случайную дату
        days_range = (end_date - start_date).days
        random_days = random.randint(0, days_range)
        current_date = start_date + timedelta(days=random_days)
        
        # Проверяем, не выходной ли это и не праздник
        if current_date.weekday() >= 5:  # Сб, Вс
            continue
        if current_date in holidays:
            continue
        
        # Выбираем учителя и ученика
        teacher = random.choice(teachers)
        student = random.choice(students)
        
        # Проверяем, есть ли уже занятие у этого учителя в это время
        start_time, end_time = random.choice(time_slots)
        
        existing = Lesson.objects.filter(
            teacher=teacher,
            date=current_date,
            start_time=start_time
        ).exists()
        
        if existing:
            continue
        
        # Определяем статус в зависимости от даты
        if current_date <= first_period_end:
            # Период 10.02-19.02: 90% проведены, 5% отменены, 5% запланированы
            rand = random.random()
            if rand < 0.9:
                status = 'completed'
            elif rand < 0.95:
                status = 'cancelled'
            else:
                status = 'scheduled'
        else:
            # После 19.02: все запланированы (будут просрочены автоматически)
            status = 'scheduled'
        
        # Выбираем предмет учителя
        subject = random.choice(list(teacher.subjects.all()))
        if not subject:
            subject = random.choice(subjects)
        
        # Выбираем платформу
        platform = random.choice(formats)
        
        # Стоимость урока (от 650 до 1000)
        cost = random.randint(650, 1000)
        # Выплата учителю (минус 100-150)
        teacher_payment = cost - random.randint(100, 150)
        
        # Создаем занятие
        lesson = Lesson.objects.create(
            teacher=teacher,
            student=student,
            subject=subject,
            format=platform,
            date=current_date,
            start_time=start_time,
            end_time=end_time,
            duration=60,
            cost=Decimal(str(cost)),
            teacher_payment=Decimal(str(teacher_payment)),
            meeting_link=f"https://zoom.us/j/{random.randint(100000, 999999)}",
            meeting_platform=platform.name,
            status=status
        )
        
        # Если занятие проведено, обновляем балансы
        if status == 'completed':
            # У ученика баланс уменьшается
            student.user.balance -= Decimal(str(cost))
            student.user.save()
            
            # У учителя баланс увеличивается
            teacher.wallet_balance += Decimal(str(teacher_payment))
            teacher.save()
            
            # Создаем платеж
            Payment.objects.create(
                user=student.user,
                amount=Decimal(str(cost)),
                payment_type='expense',
                description=f'Оплата занятия {lesson.date} ({lesson.subject.name})',
                lesson=lesson
            )
        
        lessons_created += 1
        
        if lessons_created % 10 == 0:
            print(f"  ... создано {lessons_created} занятий")
    
    print(f"  ✅ Всего создано занятий: {lessons_created}")
    
    # 6. ИТОГИ
    print("\n" + "=" * 60)
    print("ИТОГИ СОЗДАНИЯ ТЕСТОВЫХ ДАННЫХ")
    print("=" * 60)
    print(f"📚 Предметы: {Subject.objects.count()}")
    print(f"👨‍🏫 Учителя: {Teacher.objects.count()}")
    print(f"🧑‍🎓 Ученики: {Student.objects.count()}")
    print(f"📝 Занятия: {Lesson.objects.count()}")
    
    # Статистика по статусам
    print(f"\n📊 Статистика по занятиям:")
    print(f"  ✅ Проведено: {Lesson.objects.filter(status='completed').count()}")
    print(f"  📅 Запланировано: {Lesson.objects.filter(status='scheduled').count()}")
    print(f"  ❌ Отменено: {Lesson.objects.filter(status='cancelled').count()}")
    print(f"  ⏰ Просрочено: {Lesson.objects.filter(status='overdue').count()}")
    
    # Финансовая статистика
    total_teacher_balance = sum(t.wallet_balance for t in Teacher.objects.all())
    total_student_balance = sum(u.balance for u in User.objects.filter(role='student'))
    
    print(f"\n💰 Финансовая статистика:")
    print(f"  👨‍🏫 Общий баланс учителей: {total_teacher_balance:.2f} руб.")
    print(f"  🧑‍🎓 Общий баланс учеников: {total_student_balance:.2f} руб.")
    
    print("=" * 60)
    print("✅ ТЕСТОВЫЕ ДАННЫЕ УСПЕШНО СОЗДАНЫ!")
    print("=" * 60)

if __name__ == '__main__':
    create_test_data()