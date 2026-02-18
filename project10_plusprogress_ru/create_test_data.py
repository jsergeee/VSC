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
    LessonFormat, Schedule, Payment
)

def create_test_data():
    print("=" * 60)
    print("НАЧАЛО СОЗДАНИЯ ТЕСТОВЫХ ДАННЫХ")
    print("=" * 60)
    
    # 1. ПРЕДМЕТЫ
    print("\n1. СОЗДАЕМ ПРЕДМЕТЫ:")
    subjects_list = [
        'Английский язык', 'Русский язык', 'Математика', 'Физика', 'Химия',
        'Биология', 'История', 'Информатика', 'Литература', 'География'
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
    formats_list = ['Zoom', 'Voov Meeting', 'Microsoft Teams', 'Skype', 'Google Meet']
    
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
        {'first': 'Иван', 'last': 'Петров', 'patr': 'Иванович', 'subj': ['Математика', 'Физика']},
        {'first': 'Мария', 'last': 'Сидорова', 'patr': 'Алексеевна', 'subj': ['Русский язык', 'Литература']},
        {'first': 'Алексей', 'last': 'Смирнов', 'patr': 'Петрович', 'subj': ['Химия', 'Биология']},
        {'first': 'Елена', 'last': 'Козлова', 'patr': 'Дмитриевна', 'subj': ['История', 'География']},
        {'first': 'Дмитрий', 'last': 'Морозов', 'patr': 'Сергеевич', 'subj': ['Информатика', 'Математика']},
        {'first': 'Анна', 'last': 'Волкова', 'patr': 'Игоревна', 'subj': ['Английский язык']},
        {'first': 'Сергей', 'last': 'Федоров', 'patr': 'Андреевич', 'subj': ['Физика']},
        {'first': 'Ольга', 'last': 'Морозова', 'patr': 'Викторовна', 'subj': ['Биология', 'Химия']},
        {'first': 'Павел', 'last': 'Соколов', 'patr': 'Алексеевич', 'subj': ['Русский язык']},
    ]
    
    teachers = []
    for i, data in enumerate(teachers_data, 1):
        username = f"teacher_{i:02d}"
        
        # Создаем пользователя
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': data['first'],
                'last_name': data['last'],
                'patronymic': data['patr'],
                'email': f"{username}@school.ru",
                'phone': f"+7901{i:06d}",
                'role': 'teacher',
                'balance': 0
            }
        )
        
        if created:
            user.set_password('password123')
            user.save()
            print(f"  [+] {user.get_full_name()} (логин: {username}, пароль: password123)")
        else:
            print(f"  [ ] {user.get_full_name()} (уже существует)")
        
        # Создаем/получаем профиль учителя
        teacher, _ = Teacher.objects.get_or_create(user=user)
        
        # Добавляем предметы
        for subj_name in data['subj']:
            subject = Subject.objects.filter(name=subj_name).first()
            if subject:
                teacher.subjects.add(subject)
        
        teacher.experience = random.randint(3, 15)
        teacher.save()
        teachers.append(teacher)
    
        # 4. УЧЕНИКИ (30)
    print("\n4. СОЗДАЕМ УЧЕНИКОВ:")
    
    first_names = ['Александр', 'Максим', 'Артем', 'Михаил', 'Даниил', 
                   'Кирилл', 'Егор', 'Никита', 'Илья', 'Андрей',
                   'Анастасия', 'Дарья', 'Мария', 'Екатерина', 'Виктория',
                   'Полина', 'София', 'Ксения', 'Алиса', 'Валерия',
                   'Дмитрий', 'Сергей', 'Антон', 'Иван', 'Павел',
                   'Роман', 'Ольга', 'Татьяна', 'Наталья', 'Светлана']
    
    last_names = ['Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов',
                  'Попов', 'Васильев', 'Зайцев', 'Соколов', 'Михайлов',
                  'Новикова', 'Федорова', 'Морозова', 'Волкова', 'Алексеева',
                  'Лебедева', 'Семенова', 'Егорова', 'Павлова', 'Козлова',
                  'Николаев', 'Орлов', 'Макаров', 'Андреев', 'Ермаков',
                  'Ковалев', 'Ильина', 'Максимова', 'Соловьева', 'Тимофеева']
    
    students = []
    for i in range(30):
        username = f"student_{i+1:02d}"
        
        # Чередуем отчества
        if i % 3 == 0:
            patronymic = f"{first_names[i]}ович"
        elif i % 3 == 1:
            patronymic = f"{first_names[i]}овна"
        else:
            patronymic = ""
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_names[i],
                'last_name': last_names[i],
                'patronymic': patronymic,
                'email': f"{username}@student.ru",
                'phone': f"+7902{i+1:06d}",
                'role': 'student',
                'balance': Decimal(random.randint(2000, 15000))
            }
        )
        
        if created:
            user.set_password('password123')
            user.save()
            print(f"  [+] {user.get_full_name()} (логин: {username}, пароль: password123)")
        
        student, _ = Student.objects.get_or_create(user=user)
        
        # Добавляем 2-3 случайных учителя
        num_teachers = random.randint(2, 3)
        if teachers:
            selected = random.sample(teachers, min(num_teachers, len(teachers)))
            student.teachers.set(selected)
        student.save()
        students.append(student)
    
    print(f"  Всего учеников: {len(students)}")
    
    # 5. РАСПИСАНИЯ
    print("\n5. СОЗДАЕМ РАСПИСАНИЯ:")
    
    time_slots = [
        (time(10,0), time(11,0)), (time(11,0), time(12,0)), (time(13,0), time(14,0)),
        (time(14,0), time(15,0)), (time(15,0), time(16,0)), (time(16,0), time(17,0)),
        (time(17,0), time(18,0)), (time(18,0), time(19,0))
    ]
    
    schedule_count = 0
    for teacher in teachers:
        # Каждому учителю 3-5 слотов
        num_slots = random.randint(3, 5)
        days = random.sample(range(1, 6), min(num_slots, 5))  # Пн-Пт
        
        for day in days:
            start, end = random.choice(time_slots)
            _, created = Schedule.objects.get_or_create(
                teacher=teacher,
                day_of_week=day,
                start_time=start,
                end_time=end,
                defaults={'is_active': True}
            )
            if created:
                schedule_count += 1
    
    print(f"  Создано расписаний: {schedule_count}")
    
    # 6. ЗАНЯТИЯ
    print("\n6. СОЗДАЕМ ЗАНЯТИЯ НА 30 ДНЕЙ:")
    
    # Цены
    prices = {
        'Английский язык': (600, 750),
        'Русский язык': (660, 825),
        'Математика': (660, 825),
        'Физика': (720, 900),
        'Химия': (720, 900),
        'Биология': (660, 825),
        'История': (600, 750),
        'Информатика': (720, 900),
        'Литература': (660, 825),
        'География': (600, 750),
    }
    
    start_date = date.today()
    end_date = start_date + timedelta(days=30)
    
    lesson_count = 0
    current = start_date
    
    while current <= end_date:
        if current.weekday() != 6:  # Не воскресенье
            for teacher in teachers:
                schedules = Schedule.objects.filter(
                    teacher=teacher,
                    day_of_week=current.weekday(),
                    is_active=True
                )
                
                for schedule in schedules:
                    if random.random() < 0.6:  # 60% вероятность занятия
                        available = list(Student.objects.filter(teachers=teacher))
                        if not available:
                            continue
                        
                        # 30% индивидуальных, 70% групповых
                        is_individual = random.random() < 0.3
                        group_size = 1 if is_individual else random.randint(2, 3)
                        
                        selected = random.sample(
                            available, 
                            min(group_size, len(available))
                        )
                        
                        subject = random.choice(list(teacher.subjects.all()))
                        if not subject:
                            subject = subjects[0]
                        
                        platform = random.choice(formats)
                        
                        # Стоимость
                        price = prices.get(subject.name, (600, 750))
                        cost = price[1] if is_individual else price[0]
                        
                        for student in selected:
                            lesson = Lesson.objects.create(
                                teacher=teacher,
                                student=student,
                                subject=subject,
                                format=platform,
                                schedule=schedule,
                                date=current,
                                start_time=schedule.start_time,
                                end_time=schedule.end_time,
                                duration=60,
                                cost=Decimal(cost),
                                teacher_payment=Decimal(str(round(cost * 0.7, 2))),
                                meeting_link=f"https://zoom.us/j/{random.randint(100000,999999)}",
                                meeting_platform=platform.name,
                                status='scheduled'
                            )
                            lesson_count += 1
        
        current += timedelta(days=1)
        
        if lesson_count % 100 == 0 and lesson_count > 0:
            print(f"  ... создано {lesson_count} занятий")
    
    print(f"  Всего создано занятий: {lesson_count}")
    
    # ИТОГИ
    print("\n" + "=" * 60)
    print("ИТОГИ СОЗДАНИЯ ТЕСТОВЫХ ДАННЫХ")
    print("=" * 60)
    print(f"📚 Предметы: {Subject.objects.count()}")
    print(f"👨‍🏫 Учителя: {Teacher.objects.count()}")
    print(f"🧑‍🎓 Ученики: {Student.objects.count()}")
    print(f"📅 Расписания: {Schedule.objects.count()}")
    print(f"📝 Занятия: {Lesson.objects.count()}")
    print(f"📎 Форматы: {LessonFormat.objects.count()}")
    print("=" * 60)
    print("✅ ТЕСТОВЫЕ ДАННЫЕ УСПЕШНО СОЗДАНЫ!")
    print("=" * 60)

if __name__ == '__main__':
    create_test_data()