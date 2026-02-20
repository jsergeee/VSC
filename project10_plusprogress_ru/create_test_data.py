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

def calculate_teacher_payment(cost, percentage):
    """
    Расчет выплаты учителю с округлением до 50 рублей
    percentage: 0.85 для 85%, 0.9 для 90%
    """
    raw_payment = cost * percentage
    # Округляем до ближайших 50 рублей
    rounded_payment = round(raw_payment / 50) * 50
    return Decimal(str(rounded_payment))

def create_test_data():
    print("=" * 60)
    print("СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ДЛЯ ТЕСТИРОВАНИЯ АВТОМАТИЧЕСКОГО РАСЧЕТА")
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
    
    # 3. УЧИТЕЛЯ
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
    
    # 4. УЧЕНИКИ
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
                'balance': 0
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
    
    # 5. СОЗДАЕМ ЗАНЯТИЯ С РАЗНЫМИ СТАТУСАМИ
    print("\n5. СОЗДАЕМ ЗАНЯТИЯ ДЛЯ ТЕСТИРОВАНИЯ АВТОМАТИКИ:")
    
    # СЦЕНАРИЙ 1: Проведенные занятия
    print("\n   СЦЕНАРИЙ 1: Проведенные занятия")
    create_completed_lessons(students, teachers, subjects, formats)
    
    # СЦЕНАРИЙ 2: Запланированные занятия
    print("\n   СЦЕНАРИЙ 2: Запланированные занятия")
    create_scheduled_lessons(students, teachers, subjects, formats)
    
    # СЦЕНАРИЙ 3: Отмененные занятия
    print("\n   СЦЕНАРИЙ 3: Отмененные занятия")
    create_cancelled_lessons(students, teachers, subjects, formats)
    
    # СЦЕНАРИЙ 4: Просроченные занятия
    print("\n   СЦЕНАРИЙ 4: Просроченные занятия")
    create_overdue_lessons(students, teachers, subjects, formats)
    
    # СЦЕНАРИЙ 5: Занятия, которые должны стать просроченными завтра
    print("\n   СЦЕНАРИЙ 5: Занятия, которые просрочатся завтра")
    create_future_overdue_lessons(students, teachers, subjects, formats)
    
    # 6. ПРОВЕРЯЕМ РЕЗУЛЬТАТЫ
    print("\n" + "=" * 60)
    print("ПРОВЕРКА АВТОМАТИЧЕСКОГО РАСЧЕТА БАЛАНСОВ")
    print("=" * 60)
    
    check_balances()
    
    print("=" * 60)
    print("✅ ТЕСТОВЫЕ ДАННЫЕ ДЛЯ АВТОМАТИКИ СОЗДАНЫ!")
    print("=" * 60)

def create_completed_lessons(students, teachers, subjects, formats):
    """Создает проведенные занятия - должны изменить балансы"""
    count = 0
    # Длительности занятий
    durations = [45, 50, 60]
    
    for i in range(20):  # 20 проведенных занятий
        teacher = random.choice(teachers)
        student = random.choice(students)
        subject = random.choice(list(teacher.subjects.all()) or subjects)
        
        # Дата в прошлом
        lesson_date = date.today() - timedelta(days=random.randint(1, 10))
        
        # Стоимость от 650 до 1100 с шагом 50
        cost = random.choice(range(650, 1150, 50))
        
        # Случайный процент выплаты учителю (85% или 90%)
        percentage = random.choice([0.85, 0.9])
        teacher_payment = calculate_teacher_payment(cost, percentage)
        
        # Длительность занятия
        duration = random.choice(durations)
        
        # Время начала (с 9 до 19, чтобы занятие не выходило за 20:00)
        start_hour = random.randint(9, 19)
        start_minute = random.choice([0, 15, 30, 45])
        start_time = time(start_hour, start_minute)
        
        # Время окончания с учетом длительности
        end_minutes = start_hour * 60 + start_minute + duration
        end_time = time(end_minutes // 60, end_minutes % 60)
        
        lesson = Lesson.objects.create(
            teacher=teacher,
            student=student,
            subject=subject,
            format=random.choice(formats),
            date=lesson_date,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            cost=Decimal(str(cost)),
            teacher_payment=teacher_payment,
            meeting_link=f"https://zoom.us/j/{random.randint(100000, 999999)}",
            meeting_platform=random.choice(formats).name,
            status='completed'
        )
        
        # АВТОМАТИЧЕСКИЙ РАСЧЕТ: уменьшаем баланс ученика, увеличиваем баланс учителя
        student.user.balance -= Decimal(str(cost))
        student.user.save()
        
        teacher.wallet_balance += teacher_payment
        teacher.save()
        
        Payment.objects.create(
            user=student.user,
            amount=Decimal(str(cost)),
            payment_type='expense',
            description=f'Оплата проведенного занятия {lesson.date}',
            lesson=lesson
        )
        
        count += 1
        
        if count % 5 == 0:
            print(f"    ... создано {count} проведенных занятий")
    
    print(f"  ✅ Создано {count} проведенных занятий")

def create_scheduled_lessons(students, teachers, subjects, formats):
    """Создает запланированные занятия - баланс НЕ меняется"""
    count = 0
    durations = [45, 50, 60]
    
    for i in range(15):  # 15 запланированных занятий
        teacher = random.choice(teachers)
        student = random.choice(students)
        subject = random.choice(list(teacher.subjects.all()) or subjects)
        
        # Дата в будущем
        lesson_date = date.today() + timedelta(days=random.randint(1, 14))
        
        cost = random.choice(range(650, 1150, 50))
        percentage = random.choice([0.85, 0.9])
        teacher_payment = calculate_teacher_payment(cost, percentage)
        duration = random.choice(durations)
        
        start_hour = random.randint(9, 19)
        start_minute = random.choice([0, 15, 30, 45])
        start_time = time(start_hour, start_minute)
        
        end_minutes = start_hour * 60 + start_minute + duration
        end_time = time(end_minutes // 60, end_minutes % 60)
        
        Lesson.objects.create(
            teacher=teacher,
            student=student,
            subject=subject,
            format=random.choice(formats),
            date=lesson_date,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            cost=Decimal(str(cost)),
            teacher_payment=teacher_payment,
            meeting_link=f"https://zoom.us/j/{random.randint(100000, 999999)}",
            meeting_platform=random.choice(formats).name,
            status='scheduled'
        )
        count += 1
    
    print(f"  ✅ Создано {count} запланированных занятий")

def create_cancelled_lessons(students, teachers, subjects, formats):
    """Создает отмененные занятия - баланс НЕ меняется"""
    count = 0
    durations = [45, 50, 60]
    
    for i in range(5):  # 5 отмененных занятий
        teacher = random.choice(teachers)
        student = random.choice(students)
        subject = random.choice(list(teacher.subjects.all()) or subjects)
        
        # Дата может быть в прошлом или будущем
        if random.choice([True, False]):
            lesson_date = date.today() - timedelta(days=random.randint(1, 5))
        else:
            lesson_date = date.today() + timedelta(days=random.randint(1, 5))
        
        cost = random.choice(range(650, 1150, 50))
        percentage = random.choice([0.85, 0.9])
        teacher_payment = calculate_teacher_payment(cost, percentage)
        duration = random.choice(durations)
        
        start_hour = random.randint(9, 19)
        start_minute = random.choice([0, 15, 30, 45])
        start_time = time(start_hour, start_minute)
        
        end_minutes = start_hour * 60 + start_minute + duration
        end_time = time(end_minutes // 60, end_minutes % 60)
        
        Lesson.objects.create(
            teacher=teacher,
            student=student,
            subject=subject,
            format=random.choice(formats),
            date=lesson_date,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            cost=Decimal(str(cost)),
            teacher_payment=teacher_payment,
            meeting_link=f"https://zoom.us/j/{random.randint(100000, 999999)}",
            meeting_platform=random.choice(formats).name,
            status='cancelled'
        )
        count += 1
    
    print(f"  ✅ Создано {count} отмененных занятий")

def create_overdue_lessons(students, teachers, subjects, formats):
    """Создает просроченные занятия"""
    count = 0
    durations = [45, 50, 60]
    
    for i in range(8):  # 8 просроченных занятий
        teacher = random.choice(teachers)
        student = random.choice(students)
        subject = random.choice(list(teacher.subjects.all()) or subjects)
        
        # Дата в прошлом (более 24 часов назад)
        lesson_date = date.today() - timedelta(days=random.randint(2, 5))
        
        cost = random.choice(range(650, 1150, 50))
        percentage = random.choice([0.85, 0.9])
        teacher_payment = calculate_teacher_payment(cost, percentage)
        duration = random.choice(durations)
        
        start_hour = random.randint(9, 19)
        start_minute = random.choice([0, 15, 30, 45])
        start_time = time(start_hour, start_minute)
        
        end_minutes = start_hour * 60 + start_minute + duration
        end_time = time(end_minutes // 60, end_minutes % 60)
        
        Lesson.objects.create(
            teacher=teacher,
            student=student,
            subject=subject,
            format=random.choice(formats),
            date=lesson_date,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            cost=Decimal(str(cost)),
            teacher_payment=teacher_payment,
            meeting_link=f"https://zoom.us/j/{random.randint(100000, 999999)}",
            meeting_platform=random.choice(formats).name,
            status='overdue'
        )
        count += 1
    
    print(f"  ✅ Создано {count} просроченных занятий")

def create_future_overdue_lessons(students, teachers, subjects, formats):
    """Создает занятия, которые СТАНУТ просроченными завтра"""
    count = 0
    durations = [45, 50, 60]
    
    for i in range(5):  # 5 занятий, которые просрочатся завтра
        teacher = random.choice(teachers)
        student = random.choice(students)
        subject = random.choice(list(teacher.subjects.all()) or subjects)
        
        # Дата вчера (чтобы завтра стали просроченными)
        lesson_date = date.today() - timedelta(days=1)
        
        cost = random.choice(range(650, 1150, 50))
        percentage = random.choice([0.85, 0.9])
        teacher_payment = calculate_teacher_payment(cost, percentage)
        duration = random.choice(durations)
        
        start_hour = random.randint(9, 19)
        start_minute = random.choice([0, 15, 30, 45])
        start_time = time(start_hour, start_minute)
        
        end_minutes = start_hour * 60 + start_minute + duration
        end_time = time(end_minutes // 60, end_minutes % 60)
        
        Lesson.objects.create(
            teacher=teacher,
            student=student,
            subject=subject,
            format=random.choice(formats),
            date=lesson_date,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            cost=Decimal(str(cost)),
            teacher_payment=teacher_payment,
            meeting_link=f"https://zoom.us/j/{random.randint(100000, 999999)}",
            meeting_platform=random.choice(formats).name,
            status='scheduled'  # Сейчас запланированы, но вчерашняя дата!
        )
        count += 1
    
    print(f"  ✅ Создано {count} занятий, которые станут просроченными завтра")

def check_balances():
    """Проверяет корректность автоматического расчета балансов"""
    
    # Проверяем учеников
    print("\n👨‍🎓 БАЛАНСЫ УЧЕНИКОВ:")
    students_with_negative = 0
    students_with_zero = 0
    
    for student in Student.objects.all()[:10]:  # Покажем первых 10
        balance = student.user.balance
        completed_lessons_sum = sum(
            lesson.cost for lesson in Lesson.objects.filter(
                student=student, 
                status='completed'
            )
        )
        
        print(f"  {student.user.get_full_name()}: {balance} руб.")
        print(f"    Сумма проведенных занятий: {completed_lessons_sum} руб.")
        
        if balance < 0:
            students_with_negative += 1
            print(f"    ⚠️ Долг: {abs(balance)} руб.")
        elif balance == 0:
            students_with_zero += 1
    
    print(f"\n  Итого: {students_with_negative} учеников в долгу, {students_with_zero} с нулевым балансом")
    
    # Проверяем учителей
    print("\n👨‍🏫 БАЛАНСЫ УЧИТЕЛЕЙ:")
    teachers_with_positive = 0
    
    for teacher in Teacher.objects.all()[:10]:  # Покажем первых 10
        balance = teacher.wallet_balance
        completed_lessons_sum = sum(
            lesson.teacher_payment for lesson in Lesson.objects.filter(
                teacher=teacher, 
                status='completed'
            )
        )
        
        print(f"  {teacher.user.get_full_name()}: {balance} руб.")
        print(f"    Заработано за проведенные занятия: {completed_lessons_sum} руб.")
        
        if balance > 0:
            teachers_with_positive += 1
    
    print(f"\n  Итого: {teachers_with_positive} учителей с положительным балансом")
    
    # Общая статистика
    total_student_balance = sum(u.balance for u in User.objects.filter(role='student'))
    total_teacher_balance = sum(t.wallet_balance for t in Teacher.objects.all())
    
    print(f"\n💰 ОБЩАЯ СТАТИСТИКА:")
    print(f"  Суммарный долг учеников: {abs(total_student_balance):.2f} руб.")
    print(f"  Суммарный заработок учителей: {total_teacher_balance:.2f} руб.")
    
    # Проверяем консистентность
    total_lessons_cost = sum(l.cost for l in Lesson.objects.filter(status='completed'))
    total_teacher_payments = sum(l.teacher_payment for l in Lesson.objects.filter(status='completed'))
    platform_commission = total_lessons_cost - total_teacher_payments
    
    print(f"\n📊 ПРОВЕРКА КОНСИСТЕНТНОСТИ:")
    print(f"  Общая стоимость проведенных занятий: {total_lessons_cost:.2f} руб.")
    print(f"  Общая сумма выплат учителям: {total_teacher_payments:.2f} руб.")
    print(f"  Комиссия платформы: {platform_commission:.2f} руб.")
    
    if abs(abs(total_student_balance) - total_lessons_cost) < 0.01:
        print("  ✅ Балансы учеников соответствуют проведенным занятиям")
    else:
        print(f"  ⚠️ Несоответствие: долг учеников {abs(total_student_balance)} vs стоимость занятий {total_lessons_cost}")

if __name__ == '__main__':
    create_test_data()