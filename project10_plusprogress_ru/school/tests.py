from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import date, time, timedelta
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.utils import timezone
from .models import (
    User, Teacher, Student, Subject, Lesson, LessonAttendance,
    Payment, LessonReport, Notification, UserActionLog,
    Homework, HomeworkSubmission, PaymentRequest,
    GroupLesson, GroupEnrollment, Material, StudentSubjectPrice,
    Deposit, StudentNote, LessonReport, TrialRequest, ScheduleTemplate,
)

User = get_user_model()


class APITestCase(APITestCase):
    """Базовый класс для тестов API"""

    def setUp(self):
        """Настройка перед каждым тестом"""
        # Создаем тестового админа
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )

        # Создаем токен для админа
        self.admin_token = Token.objects.create(user=self.admin_user)

        # Создаем тестового учителя
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            password='teacher123',
            first_name='Иван',
            last_name='Петров',
            role='teacher'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            bio='Опытный преподаватель',
            experience=5
        )

        # Создаем тестового ученика
        self.student_user = User.objects.create_user(
            username='student1',
            password='student123',
            first_name='Петр',
            last_name='Сидоров',
            role='student'
        )
        self.student = Student.objects.create(user=self.student_user)
        self.student.teachers.add(self.teacher)

        # Создаем предмет
        self.subject = Subject.objects.create(name='Математика')
        self.teacher.subjects.add(self.subject)

        # Настраиваем клиент
        self.client = APIClient()


class RegistrationTests(APITestCase):
    """Тесты регистрации пользователей"""

    def test_user_registration_success(self):
        """Тест успешной регистрации"""
        url = reverse('api-register')
        data = {
            'username': 'newuser',
            'password': 'password123',
            'password2': 'password123',
            'email': 'newuser@test.com',
            'first_name': 'Новый',
            'last_name': 'Пользователь',
            'phone': '+79991112233'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'newuser')
        self.assertEqual(response.data['user']['role'], 'student')

        # Проверяем, что ученик создан
        user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(user, 'student_profile'))

        # Проверяем, что токен создан
        token = Token.objects.get(user=user)
        self.assertEqual(token.key, response.data['token'])

    def test_user_registration_password_mismatch(self):
        """Тест несовпадения паролей"""
        url = reverse('api-register')
        data = {
            'username': 'newuser',
            'password': 'password123',
            'password2': 'different123',
            'email': 'newuser@test.com'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_duplicate_username(self):
        """Тест дубликата имени пользователя"""
        url = reverse('api-register')
        data = {
            'username': 'newuser',
            'password': 'password123',
            'password2': 'password123',
            'email': 'newuser@test.com'
        }

        # Первая регистрация - успех
        response1 = self.client.post(url, data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Вторая регистрация с тем же username - ошибка
        response2 = self.client.post(url, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    """Тесты авторизации"""

    def test_login_success(self):
        """Тест успешного логина"""
        url = reverse('api-login')
        data = {
            'username': 'teacher1',
            'password': 'teacher123'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user_id', response.data)
        self.assertIn('role', response.data)
        self.assertEqual(response.data['username'], 'teacher1')
        self.assertEqual(response.data['role'], 'teacher')

    def test_login_invalid_credentials(self):
        """Тест неверных учетных данных"""
        url = reverse('api-login')
        data = {
            'username': 'teacher1',
            'password': 'wrongpassword'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TeacherAPITests(APITestCase):
    """Тесты API для учителей"""

    def test_create_teacher_as_admin(self):
        """Тест создания учителя администратором"""
        url = reverse('teacher-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')

        data = {
            'user': {
                'username': 'newteacher',
                'password': 'teacher123',
                'first_name': 'Новый',
                'last_name': 'Учитель',
                'email': 'newteacher@test.com'
            },
            'subjects': [self.subject.id],
            'bio': 'Новый преподаватель',
            'experience': 3
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['username'], 'newteacher')
        self.assertEqual(response.data['user']['role'], 'teacher')

    def test_create_teacher_without_auth(self):
        """Тест создания учителя без авторизации"""
        url = reverse('teacher-list')
        data = {
            'user': {
                'username': 'newteacher',
                'password': 'teacher123',
                'first_name': 'Новый',
                'last_name': 'Учитель'
            },
            'subjects': [self.subject.id]
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_teachers(self):
        """Тест получения списка учителей"""
        url = reverse('teacher-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)


class StudentAPITests(APITestCase):
    """Тесты API для учеников"""

    def test_create_student_as_admin(self):
        """Тест создания ученика администратором"""
        url = reverse('student-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')

        data = {
            'user': {
                'username': 'newstudent',
                'password': 'student123',
                'first_name': 'Новый',
                'last_name': 'Ученик',
                'email': 'newstudent@test.com'
            },
            'teachers': [self.teacher.id],
            'parent_name': 'Родитель',
            'parent_phone': '+79990000000'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['username'], 'newstudent')
        self.assertEqual(response.data['user']['role'], 'student')

    def test_filter_student_by_user_id(self):
        """Тест фильтрации ученика по user_id"""
        # Добавляем метод фильтрации в ViewSet
        url = reverse('student-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')

        # Тест с фильтром
        response = self.client.get(url, {'user_id': self.student_user.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user']['id'], self.student_user.id)


class LessonAPITests(APITestCase):
    """Тесты API для уроков"""

    def setUp(self):
        super().setUp()
        # Создаем второго ученика для группового урока
        self.student2_user = User.objects.create_user(
            username='student2',
            password='student123',
            first_name='Второй',
            last_name='Ученик',
            role='student'
        )
        self.student2 = Student.objects.create(user=self.student2_user)
        self.student2.teachers.add(self.teacher)

    def test_create_lesson_with_students(self):
        """Тест создания урока с учениками"""
        url = reverse('lesson-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')

        data = {
            'teacher': self.teacher.id,
            'subject': self.subject.id,
            'date': '2026-03-15',
            'start_time': '10:00:00',
            'end_time': '11:00:00',
            'price_type': 'per_student',
            'base_cost': 1000,
            'base_teacher_payment': 700,
            'students_data': [
                {
                    'student_id': self.student.id,
                    'cost': 1000,
                    'teacher_payment': 700
                },
                {
                    'student_id': self.student2.id,
                    'cost': 1000,
                    'teacher_payment': 700
                }
            ]
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['teacher'], self.teacher.id)
        self.assertEqual(response.data['subject'], self.subject.id)

        # Проверяем, что урок создан и ученики привязаны
        lesson = Lesson.objects.get(id=response.data['id'])
        self.assertEqual(lesson.attendance.count(), 2)

    def test_list_lessons(self):
        """Тест получения списка уроков"""
        url = reverse('lesson-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TokenTests(APITestCase):
    """Тесты для токенов"""

    def test_token_authentication(self):
        """Тест аутентификации по токену"""
        # Создаем ученика через API
        register_url = reverse('api-register')
        register_data = {
            'username': 'testuser',
            'password': 'test1234',
            'password2': 'test1234',
            'email': 'test@test.com',
            'first_name': 'Тест',
            'last_name': 'Пользователь',
            'phone': '+79991112233'
        }

        register_response = self.client.post(register_url, register_data, format='json')
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

        token = register_response.data['token']

        # Используем токен
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        # Получаем свои данные через специальный endpoint
        me_url = reverse('student-me')
        response = self.client.get(me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['id'], register_response.data['user']['id'])

    def test_student_can_access_own_data(self):
        """Тест: ученик может получить свои данные"""
        # Создаем ученика
        register_url = reverse('api-register')
        register_data = {
            'username': 'ownertest',
            'password': 'test1234',
            'password2': 'test1234',
            'email': 'owner@test.com',
            'first_name': 'Owner',
            'last_name': 'Test',
            'phone': '+79991112255'
        }

        register_response = self.client.post(register_url, register_data, format='json')
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

        token = register_response.data['token']

        # Используем токен
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        # Получаем свои данные через me endpoint
        me_url = reverse('student-me')
        response = self.client.get(me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], 'ownertest')

    def test_invalid_token(self):
        """Тест невалидного токена"""
        self.client.credentials(HTTP_AUTHORIZATION='Token invalidtoken123')

        students_url = reverse('student-list')
        response = self.client.get(students_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_after_registration(self):
        """Тест логина после регистрации"""
        # Сначала регистрируемся
        register_url = reverse('api-register')
        register_data = {
            'username': 'logintest',
            'password': 'test1234',
            'password2': 'test1234',
            'email': 'login@test.com',
            'first_name': 'Login',
            'last_name': 'Test',
            'phone': '+79991112244'
        }

        register_response = self.client.post(register_url, register_data, format='json')
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

        # Теперь логинимся
        login_url = reverse('api-login')
        login_data = {
            'username': 'logintest',
            'password': 'test1234'
        }

        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('token', login_response.data)
        self.assertEqual(login_response.data['username'], 'logintest')


class UserModelTest(TestCase):
    """Тесты модели пользователя"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Иван',
            last_name='Петров',
            patronymic='Сергеевич',
            email='test@test.com',
            phone='+79991234567',
            role='student'
        )

    def test_get_full_name(self):
        """Тест правильного формирования ФИО"""
        self.assertEqual(
            self.user.get_full_name(),
            'Петров Иван Сергеевич'
        )

    def test_str_method(self):
        """Тест строкового представления"""
        self.assertEqual(str(self.user), 'Петров Иван Сергеевич')

    def test_balance_calculated(self):
        """Тест расчета баланса"""
        # Создаем платеж (пополнение)
        Payment.objects.create(
            user=self.user,
            amount=1000,
            payment_type='income',
            description='Пополнение'
        )

        self.assertEqual(self.user.balance_calculated, 1000)


class StudentModelTest(TestCase):
    """Тесты модели ученика"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='student',
            password='testpass123',
            first_name='Иван',
            last_name='Петров',
            patronymic='Сергеевич',
            role='student'
        )
        self.student = Student.objects.create(user=self.user)

        self.subject = Subject.objects.create(name='Математика')

        self.teacher_user = User.objects.create_user(
            username='teacher',
            password='testpass123',
            first_name='Мария',
            last_name='Иванова',
            role='teacher'
        )
        self.teacher = Teacher.objects.create(user=self.teacher_user)
        self.teacher.subjects.add(self.subject)

        self.lesson = Lesson.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            base_cost=Decimal('1000'),
            base_teacher_payment=Decimal('700')
        )

        self.attendance = LessonAttendance.objects.create(
            lesson=self.lesson,
            student=self.student,
            cost=Decimal('1000'),
            teacher_payment_share=Decimal('700'),
            status='attended'
        )

    def test_student_balance(self):
        """Тест баланса ученика"""
        Payment.objects.create(
            user=self.user,
            amount=2000,
            payment_type='income',
            description='Пополнение'
        )

        # Баланс = пополнения - стоимость уроков
        self.assertEqual(self.user.get_balance(), 1000)

    def test_attended_lessons_count(self):
        """Тест количества пройденных уроков"""
        self.assertEqual(self.student.attended_lessons_count, 1)


class TeacherModelTest(TestCase):
    """Тесты модели учителя"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='teacher',
            password='testpass123',
            first_name='Мария',
            last_name='Иванова',
            role='teacher'
        )
        self.teacher = Teacher.objects.create(user=self.user)

        self.subject = Subject.objects.create(name='Математика')
        self.teacher.subjects.add(self.subject)

        self.student_user = User.objects.create_user(
            username='student',
            password='testpass123',
            first_name='Иван',
            last_name='Петров',
            role='student'
        )
        self.student = Student.objects.create(user=self.student_user)

        self.lesson = Lesson.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            base_cost=Decimal('1000'),
            base_teacher_payment=Decimal('700'),
            status='completed'
        )

        LessonAttendance.objects.create(
            lesson=self.lesson,
            student=self.student,
            cost=Decimal('1000'),
            teacher_payment_share=Decimal('700'),
            status='attended'
        )

    def test_teacher_earnings(self):
        """Тест расчета заработка учителя"""
        start_date = date.today() - timedelta(days=30)
        end_date = date.today() + timedelta(days=30)

        earnings = self.teacher.get_teacher_earnings(start_date, end_date)

        self.assertEqual(earnings['total_payments'], 1000)
        self.assertEqual(earnings['total_salaries'], 700)
        self.assertEqual(earnings['commission'], 300)


class LessonModelTest(TestCase):
    """Тесты модели урока"""

    def setUp(self):
        # Создаем тестовые данные
        self.teacher_user = User.objects.create_user(
            username='teacher',
            password='testpass123',
            first_name='Мария',
            last_name='Иванова',
            role='teacher'
        )
        self.teacher = Teacher.objects.create(user=self.teacher_user)

        self.subject = Subject.objects.create(name='Математика')

        self.student_user = User.objects.create_user(
            username='student',
            password='testpass123',
            first_name='Иван',
            last_name='Петров',
            role='student'
        )
        self.student = Student.objects.create(user=self.student_user)

        self.lesson = Lesson.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            base_cost=Decimal('1000'),
            base_teacher_payment=Decimal('700')
        )

    def test_lesson_creation(self):
        """Тест создания урока"""
        self.assertEqual(self.lesson.subject.name, 'Математика')
        self.assertEqual(self.lesson.teacher.user.first_name, 'Мария')

    def test_add_student(self):
        """Тест добавления ученика к уроку"""
        attendance = LessonAttendance.objects.create(
            lesson=self.lesson,
            student=self.student,
            cost=Decimal('1000'),
            teacher_payment_share=Decimal('700')
        )

        self.assertEqual(self.lesson.students.count(), 1)
        self.assertEqual(attendance.status, 'registered')

    def test_mark_completed(self):
        """Тест завершения урока"""
        attendance = LessonAttendance.objects.create(
            lesson=self.lesson,
            student=self.student,
            cost=Decimal('1000'),
            teacher_payment_share=Decimal('700')
        )

        # Отмечаем посещаемость
        attendance.status = 'attended'
        attendance.save()

        # Завершаем урок
        self.lesson.status = 'completed'
        self.lesson.save()

        self.assertEqual(self.lesson.status, 'completed')


class PaymentModelTest(TestCase):
    """Тесты модели платежей"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Иван',
            last_name='Петров',
            role='student'
        )

    def test_income_payment(self):
        """Тест пополнения баланса"""
        payment = Payment.objects.create(
            user=self.user,
            amount=1000,
            payment_type='income',
            description='Пополнение'
        )

        self.assertEqual(payment.payment_type, 'income')
        self.assertEqual(payment.amount, 1000)

    def test_expense_payment(self):
        """Тест списания"""
        payment = Payment.objects.create(
            user=self.user,
            amount=500,
            payment_type='expense',
            description='Списание'
        )

        self.assertEqual(payment.payment_type, 'expense')
        self.assertEqual(payment.amount, 500)


class ViewTest(TestCase):
    """Тесты представлений"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Иван',
            last_name='Петров',
            role='student',
            is_email_verified=True
        )

        self.teacher_user = User.obtetsjects.create_user(
            username='teacher',
            password='testpass123',
            first_name='Мария',
            last_name='Иванова',
            role='teacher',
            is_email_verified=True
        )
        # 👇 ДОБАВЬТЕ ЭТУ СТРОКУ
        self.teacher = Teacher.objects.create(user=self.teacher_user)


class AdminTest(TestCase):
    """Тесты админ-панели"""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        self.client.login(username='admin', password='admin123')

    def test_admin_index(self):
        """Тест главной страницы админки"""
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def test_user_admin_list(self):
        """Тест списка пользователей в админке"""
        response = self.client.get('/admin/school/user/')
        self.assertEqual(response.status_code, 200)

    def test_student_admin_list(self):
        """Тест списка учеников в админке"""
        response = self.client.get('/admin/school/student/')
        self.assertEqual(response.status_code, 200)

    def test_teacher_admin_list(self):
        """Тест списка учителей в админке"""
        response = self.client.get('/admin/school/teacher/')
        self.assertEqual(response.status_code, 200)


class LoggingTest(TestCase):
    """Тесты системы логирования"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Иван',
            last_name='Петров',
            role='student',
            is_email_verified=True
        )

    def test_login_logging(self):
        """Тест логирования входа"""
        self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })

        logs = UserActionLog.objects.filter(
            user=self.user,
            action_type='login'
        )
        self.assertEqual(logs.count(), 1)

    def test_logout_logging(self):
        """Тест логирования выхода"""
        self.client.login(username='testuser', password='testpass123')
        self.client.get(reverse('logout'))

        logs = UserActionLog.objects.filter(
            user=self.user,
            action_type='logout'
        )
        self.assertEqual(logs.count(), 1)


# Функциональные тесты
class FunctionalTest(TestCase):
    """Комплексные тесты"""

    def setUp(self):
        self.client = Client()

        # Создаем учителя
        self.teacher_user = User.objects.create_user(
            username='teacher',
            password='testpass123',
            first_name='Мария',
            last_name='Иванова',
            role='teacher',
            is_email_verified=True
        )
        self.teacher = Teacher.objects.create(user=self.teacher_user)

        # Создаем ученика
        self.student_user = User.objects.create_user(
            username='student',
            password='testpass123',
            first_name='Иван',
            last_name='Петров',
            role='student',
            is_email_verified=True
        )
        self.student = Student.objects.create(user=self.student_user)

        # Создаем предмет
        self.subject = Subject.objects.create(name='Математика')
        self.teacher.subjects.add(self.subject)

    def test_full_lesson_flow(self):
        """Тест полного цикла урока"""
        # 1. Ученик пополняет баланс
        Payment.objects.create(
            user=self.student_user,
            amount=2000,
            payment_type='income',
            description='Пополнение'
        )

        # 2. Создаем урок
        lesson = Lesson.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            base_cost=Decimal('1000'),
            base_teacher_payment=Decimal('700')
        )

        # 3. Добавляем ученика
        attendance = LessonAttendance.objects.create(
            lesson=lesson,
            student=self.student,
            cost=Decimal('1000'),
            teacher_payment_share=Decimal('700')
        )

        # 4. Проводим урок
        attendance.status = 'attended'
        attendance.save()
        lesson.status = 'completed'
        lesson.save()

        # 5. Проверяем баланс ученика
        self.assertEqual(self.student_user.get_balance(), 1000)

        # 6. Проверяем выплату учителю
        earnings = self.teacher.get_teacher_earnings(
            date.today() - timedelta(days=30),
            date.today() + timedelta(days=30)
        )
        self.assertEqual(earnings['total_salaries'], 700)


class HomeworkModelTest(TestCase):
    """Тесты модели домашнего задания"""

    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username='teacher',
            password='testpass123',
            first_name='Мария',
            last_name='Иванова',
            role='teacher'
        )
        self.teacher = Teacher.objects.create(user=self.teacher_user)

        self.student_user = User.objects.create_user(
            username='student',
            password='testpass123',
            first_name='Иван',
            last_name='Петров',
            role='student'
        )
        self.student = Student.objects.create(user=self.student_user)

        self.subject = Subject.objects.create(name='Математика')
        self.teacher.subjects.add(self.subject)

        self.homework = Homework.objects.create(
            teacher=self.teacher,
            student=self.student,
            subject=self.subject,
            title='Тестовое задание',
            description='Описание задания',
            deadline=timezone.now() + timedelta(days=7)
        )

    def test_homework_creation(self):
        """Тест создания домашнего задания"""
        self.assertEqual(self.homework.title, 'Тестовое задание')
        self.assertEqual(self.homework.get_status(), 'pending')

    def test_homework_submission(self):
        """Тест сдачи домашнего задания"""
        submission = HomeworkSubmission.objects.create(
            homework=self.homework,
            student=self.student,
            answer_text='Ответ ученика',
            status='submitted'
        )

        self.assertEqual(self.homework.get_status(), 'submitted')
        self.assertEqual(submission.status, 'submitted')

    def test_homework_check(self):
        """Тест проверки домашнего задания"""
        submission = HomeworkSubmission.objects.create(
            homework=self.homework,
            student=self.student,
            answer_text='Ответ ученика',
            status='submitted'
        )

        submission.status = 'checked'
        submission.grade = 5
        submission.teacher_comment = 'Отлично!'
        submission.save()

        self.assertEqual(self.homework.get_status(), 'checked')
        self.assertEqual(submission.grade, 5)


class PaymentRequestModelTest(TestCase):
    """Тесты модели запроса выплаты"""

    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username='teacher',
            password='testpass123',
            first_name='Мария',
            last_name='Иванова',
            role='teacher'
        )
        self.teacher = Teacher.objects.create(user=self.teacher_user)

        self.payment_request = PaymentRequest.objects.create(
            teacher=self.teacher,
            amount=Decimal('5000'),
            payment_method='bank_card',
            payment_details='1234 5678 9012 3456',
            status='pending'
        )

    def test_payment_request_creation(self):
        """Тест создания запроса на выплату"""
        self.assertEqual(self.payment_request.amount, 5000)
        self.assertEqual(self.payment_request.status, 'pending')

    def test_payment_request_approve(self):
        """Тест одобрения запроса"""
        self.payment_request.approve(self.teacher_user)
        self.assertEqual(self.payment_request.status, 'approved')

    def test_payment_request_reject(self):
        """Тест отклонения запроса"""
        self.payment_request.reject(self.teacher_user, 'Недостаточно средств')
        self.assertEqual(self.payment_request.status, 'rejected')
        self.assertEqual(self.payment_request.comment, 'Недостаточно средств')


class MaterialModelTest(TestCase):
    """Тесты модели методических материалов"""

    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username='teacher',
            password='testpass123',
            first_name='Мария',
            last_name='Иванова',
            role='teacher'
        )
        self.teacher = Teacher.objects.create(user=self.teacher_user)

        self.subject = Subject.objects.create(name='Математика')

        self.material = Material.objects.create(
            title='Тестовый материал',
            description='Описание материала',
            material_type='file',
            created_by=self.teacher_user,
            is_public=True
        )
        self.material.subjects.add(self.subject)
        self.material.teachers.add(self.teacher)

    def test_material_creation(self):
        """Тест создания материала"""
        self.assertEqual(self.material.title, 'Тестовый материал')
        self.assertTrue(self.material.is_public)
        self.assertEqual(self.material.subjects.count(), 1)


class TeacherDashboardHomeworkTest(TestCase):
    """Тесты домашних заданий в дашборде учителя"""

    def setUp(self):
        self.client = Client()

        # Создаем учителя
        self.teacher_user = User.objects.create_user(
            username='teacher',
            password='testpass123',
            first_name='Мария',
            last_name='Иванова',
            role='teacher',
            is_email_verified=True,
            telegram_chat_id='123456',
            telegram_notifications=True
        )
        self.teacher = Teacher.objects.create(user=self.teacher_user)

        # Создаем ученика
        self.student_user = User.objects.create_user(
            username='student',
            password='testpass123',
            first_name='Иван',
            last_name='Петров',
            role='student',
            is_email_verified=True
        )
        self.student = Student.objects.create(user=self.student_user)
        self.student.teachers.add(self.teacher)

        # Создаем предмет
        self.subject = Subject.objects.create(name='Математика')
        self.teacher.subjects.add(self.subject)

        # Логиним учителя
        self.client.login(username='teacher', password='testpass123')

    def test_teacher_dashboard_homeworks_display(self):
        """Тест отображения домашних заданий в дашборде"""
        # Создаем домашнее задание
        homework = Homework.objects.create(
            teacher=self.teacher,
            student=self.student,
            subject=self.subject,
            title='Тестовое задание',
            description='Описание',
            deadline=timezone.now() + timedelta(days=7)
        )

        response = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовое задание')
        self.assertContains(response, 'Петров Иван')

    def test_teacher_homework_create_view(self):
        """Тест создания домашнего задания из дашборда"""
        response = self.client.post(reverse('teacher_homework_create'), {
            'student': self.student.id,
            'subject': self.subject.id,
            'title': 'Новое задание',
            'description': 'Подробное описание',
            'deadline': (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M')
        })

        # Должен быть редирект на страницу деталей
        self.assertEqual(response.status_code, 302)

        # Проверяем, что задание создалось
        homework = Homework.objects.filter(title='Новое задание').first()
        self.assertIsNotNone(homework)
        self.assertEqual(homework.teacher, self.teacher)
        self.assertEqual(homework.student, self.student)

    def test_teacher_homework_detail_view(self):
        """Тест просмотра деталей домашнего задания"""
        homework = Homework.objects.create(
            teacher=self.teacher,
            student=self.student,
            subject=self.subject,
            title='Тестовое задание',
            description='Описание',
            deadline=timezone.now() + timedelta(days=7)
        )

        response = self.client.get(reverse('teacher_homework_detail', args=[homework.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовое задание')
        self.assertContains(response, 'Петров Иван')


class TeacherHomeworkStatsTest(TestCase):
    """Тесты статистики домашних заданий в дашборде"""

    def setUp(self):
        self.client = Client()

        self.teacher_user = User.objects.create_user(
            username='teacher',
            password='testpass123',
            first_name='Мария',
            last_name='Иванова',
            role='teacher',
            is_email_verified=True
        )
        self.teacher = Teacher.objects.create(user=self.teacher_user)

        self.student1 = Student.objects.create(
            user=User.objects.create_user(
                username='student1',
                password='testpass123',
                first_name='Иван',
                last_name='Петров',
                role='student'
            )
        )
        self.student2 = Student.objects.create(
            user=User.objects.create_user(
                username='student2',
                password='testpass123',
                first_name='Анна',
                last_name='Сидорова',
                role='student'
            )
        )

        self.student1.teachers.add(self.teacher)
        self.student2.teachers.add(self.teacher)

        self.subject = Subject.objects.create(name='Математика')
        self.teacher.subjects.add(self.subject)

        self.client.login(username='teacher', password='testpass123')

    def test_homework_stats_calculation(self):
        """Тест расчета статистики домашних заданий"""
        # Создаем разные типы заданий
        # 1. Ожидающее (pending)
        homework1 = Homework.objects.create(
            teacher=self.teacher,
            student=self.student1,
            subject=self.subject,
            title='Задание 1',
            description='Описание 1',
            deadline=timezone.now() + timedelta(days=7)
        )

        # 2. Сданное на проверку (submitted)
        homework2 = Homework.objects.create(
            teacher=self.teacher,
            student=self.student2,
            subject=self.subject,
            title='Задание 2',
            description='Описание 2',
            deadline=timezone.now() + timedelta(days=5)
        )
        HomeworkSubmission.objects.create(
            homework=homework2,
            student=self.student2,
            answer_text='Ответ ученика',
            status='submitted'
        )

        # 3. Проверенное (checked)
        homework3 = Homework.objects.create(
            teacher=self.teacher,
            student=self.student1,
            subject=self.subject,
            title='Задание 3',
            description='Описание 3',
            deadline=timezone.now() - timedelta(days=1)
        )
        submission = HomeworkSubmission.objects.create(
            homework=homework3,
            student=self.student1,
            answer_text='Ответ ученика',
            status='checked'
        )
        submission.status = 'checked'
        submission.grade = 5
        submission.save()

        response = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(response.status_code, 200)

        # Проверяем, что в контексте есть статистика
        self.assertIn('homework_stats', response.context)
        stats = response.context['homework_stats']

        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['pending'], 1)  # homework1
        self.assertEqual(stats['submitted'], 1)  # homework2
        self.assertEqual(stats['checked'], 1)  # homework3


class TeacherHomeworkCheckTest(TestCase):
    """Тесты проверки домашних заданий"""

    def setUp(self):
        self.client = Client()

        self.teacher_user = User.objects.create_user(
            username='teacher',
            password='testpass123',
            first_name='Мария',
            last_name='Иванова',
            role='teacher',
            is_email_verified=True
        )
        self.teacher = Teacher.objects.create(user=self.teacher_user)

        self.student_user = User.objects.create_user(
            username='student',
            password='testpass123',
            first_name='Иван',
            last_name='Петров',
            role='student',
            is_email_verified=True
        )
        self.student = Student.objects.create(user=self.student_user)
        self.student.teachers.add(self.teacher)

        self.subject = Subject.objects.create(name='Математика')
        self.teacher.subjects.add(self.subject)

        self.homework = Homework.objects.create(
            teacher=self.teacher,
            student=self.student,
            subject=self.subject,
            title='Тестовое задание',
            description='Описание',
            deadline=timezone.now() + timedelta(days=7)
        )

        self.submission = HomeworkSubmission.objects.create(
            homework=self.homework,
            student=self.student,
            answer_text='Ответ ученика',
            status='submitted'
        )

        self.client.login(username='teacher', password='testpass123')

    def test_teacher_check_homework(self):
        """Тест проверки домашнего задания"""
        response = self.client.post(
            reverse('teacher_homework_detail', args=[self.homework.id]),
            {
                'grade': 5,
                'teacher_comment': 'Отличная работа!'
            }
        )

        # Обновляем из базы
        self.submission.refresh_from_db()

        self.assertEqual(self.submission.status, 'checked')
        self.assertEqual(self.submission.grade, 5)
        self.assertEqual(self.submission.teacher_comment, 'Отличная работа!')

        # Проверяем, что создалось уведомление
        notification = Notification.objects.filter(
            user=self.student_user,
            notification_type='homework_checked'
        ).first()
        self.assertIsNotNone(notification)


def test_full_homework_flow(self):
    """Тест полного цикла домашнего задания"""
    # Логиним учителя
    self.client.login(username='teacher', password='testpass123')

    # 1. Создаем домашнее задание
    response = self.client.post(reverse('teacher_homework_create'), {
        'student': self.student.id,
        'subject': self.subject.id,
        'title': 'Домашнее задание',
        'description': 'Решить задачи',
        'deadline': (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M')
    })
    self.assertEqual(response.status_code, 302)

    homework = Homework.objects.get(title='Домашнее задание')

    # 2. Логиним ученика и сдаем задание
    self.client.logout()
    self.client.login(username='student', password='testpass123')

    response = self.client.post(
        reverse('student_homework_submit', args=[homework.id]),
        {'answer_text': 'Мое решение'}
    )

    # 3. Логиним учителя и проверяем
    self.client.logout()
    self.client.login(username='teacher', password='testpass123')

    response = self.client.post(
        reverse('teacher_homework_detail', args=[homework.id]),
        {'grade': 5, 'teacher_comment': 'Отлично!'}
    )

    # 4. Проверяем результат
    submission = HomeworkSubmission.objects.get(homework=homework)
    self.assertEqual(submission.status, 'checked')
    self.assertEqual(submission.grade, 5)


class MaterialAPITests(APITestCase):
    """Тесты API для методических материалов"""

    def setUp(self):
        super().setUp()  # 👈 ВАЖНО: вызываем setUp родительского класса
        # Создаем токен для ученика
        self.student_token = Token.objects.create(user=self.student_user)

    def test_create_material_as_teacher(self):
        """Тест создания материала учителем"""
        url = reverse('material-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')

        data = {
            'title': 'Тестовый материал',
            'description': 'Описание материала',
            'material_type': 'link',
            'link': 'https://example.com',
            'is_public': True,
            'subjects': [self.subject.id],
            'students': [self.student.id]
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Тестовый материал')

    def test_list_materials_student(self):
        """Тест получения материалов учеником"""
        # Создаем публичный материал
        Material.objects.create(
            title='Публичный материал',
            material_type='link',
            link='https://example.com',
            is_public=True
        )

        # Логинимся как ученик (используем созданный токен)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.student_token.key}')
        url = reverse('material-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GroupLessonAPITests(APITestCase):
    """Тесты API для групповых уроков"""

    def setUp(self):
        super().setUp()
        self.student2_user = User.objects.create_user(
            username='student2',
            password='test123',
            first_name='Анна',
            last_name='Сидорова',
            role='student'
        )
        self.student2 = Student.objects.create(user=self.student2_user)

    def test_create_group_lesson(self):
        """Тест создания группового урока"""
        url = reverse('grouplesson-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')

        data = {
            'teacher': self.teacher.id,
            'subject': self.subject.id,
            'date': '2026-03-20',
            'start_time': '15:00:00',
            'end_time': '16:30:00',
            'price_type': 'per_student',
            'base_price': 800,
            'teacher_payment': 5000,
            'teacher_payment': 500
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_enroll_student(self):
        """Тест записи ученика на групповой урок"""
        # Создаем урок - используем time objects, а не строки
        from datetime import time

        lesson = GroupLesson.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            date='2026-03-20',
            start_time=time(15, 0),  # 👈 15:00 как объект time
            end_time=time(16, 30),  # 👈 16:30 как объект time
            price_type='per_student',
            base_price=800,
            teacher_payment=500
        )

        url = reverse('grouplesson-enroll', args=[lesson.id])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')

        response = self.client.post(url, {'student_id': self.student.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(lesson.enrollments.count(), 1)
class ScheduleTemplateAPITests(APITestCase):
    """Тесты API для шаблонов расписания"""

    def test_create_schedule_template(self):
        """Тест создания шаблона расписания"""
        url = reverse('scheduletemplate-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')

        data = {
            'teacher': self.teacher.id,
            'subject': self.subject.id,
            'start_time': '10:00:00',
            'end_time': '11:00:00',
            'repeat_type': 'weekly',
            'monday': True,
            'wednesday': True,
            'friday': True,
            'start_date': '2026-04-01',
            'end_date': '2026-06-30',
            'students': [self.student.id]
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class StudentSubjectPriceAPITests(APITestCase):
    """Тесты API для индивидуальных цен"""

    def test_create_student_price(self):
        """Тест создания индивидуальной цены"""
        url = reverse('studentsubjectprice-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')

        data = {
            'student': self.student.id,
            'teacher': self.teacher.id,
            'subject': self.subject.id,
            'cost': 1200,
            'teacher_payment': 800
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TrialRequestAPITests(APITestCase):
    """Тесты API для заявок на пробный урок"""

    def test_create_trial_request_without_auth(self):
        """Тест создания заявки без авторизации"""
        url = reverse('trialrequest-list')
        self.client.credentials()  # Убираем авторизацию

        data = {
            'name': 'Иван Петров',
            'email': 'ivan@mail.ru',
            'phone': '+79991234567',
            'subject': 'Математика'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class DepositAPITests(APITestCase):
    """Тесты API для депозитов"""

    def setUp(self):
        super().setUp()
        # Создаем токен для админа (он уже есть в родительском классе)

    def test_create_deposit(self):
        """Тест создания депозита"""
        url = reverse('deposit-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')

        data = {
            'student': self.student.id,
            'amount': 5000,
            'description': 'Пополнение счета'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что депозит создался
        self.assertEqual(response.data['amount'], '5000.00')
        self.assertEqual(response.data['student'], self.student.id)

        # 👇 ВАРИАНТ 1: Проверяем что баланс обновился (если это происходит автоматически)
        # self.student.user.refresh_from_db()
        # self.assertEqual(self.student.user.balance, 5000)

        deposit = Deposit.objects.filter(student=self.student).first()
        self.assertIsNotNone(deposit)
        self.assertEqual(deposit.amount, 5000)


class StudentNoteAPITests(APITestCase):
    """Тесты API для заметок об учениках"""

    def setUp(self):
        super().setUp()
        # Создаем токен для учителя
        self.teacher_token = Token.objects.create(user=self.teacher_user)

    def test_create_student_note(self):
        """Тест создания заметки"""
        url = reverse('studentnote-list')
        # Используем токен учителя, а не объект пользователя
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token.key}')

        data = {
            'teacher': self.teacher.id,
            'student': self.student.id,
            'text': 'Способный ученик'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class PaymentRequestAPITests(APITestCase):
    """Тесты API для запросов на выплаты"""

    # 👇 УБИРАЕМ setUp - он не нужен, токен админа уже есть в родительском классе

    def test_create_payment_request(self):
        """Тест создания запроса на выплату"""
        # Добавляем баланс учителю
        self.teacher.wallet_balance = 10000
        self.teacher.save()

        url = reverse('paymentrequest-list')
        # 👇 ИСПОЛЬЗУЕМ СУЩЕСТВУЮЩИЙ ТОКЕН АДМИНА
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')

        data = {
            'teacher': self.teacher.id,
            'amount': 5000,
            'payment_method': 'bank_card',
            'payment_details': '1234 5678 9012 3456'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class LessonReportAPITests(APITestCase):
    """Тесты API для отчетов о уроках"""

    def setUp(self):
        super().setUp()
        # 👇 СОЗДАЕМ ТОКЕН ДЛЯ УЧИТЕЛЯ (ЭТОГО НЕ ХВАТАЛО)
        self.teacher_token = Token.objects.create(user=self.teacher_user)

        # Создаем урок
        self.lesson = Lesson.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            base_cost=1000
        )
        LessonAttendance.objects.create(
            lesson=self.lesson,
            student=self.student,
            cost=1000,
            teacher_payment_share=700
        )

    def test_create_lesson_report(self):
        """Тест создания отчета"""
        url = reverse('lessonreport-list')
        # 👇 ТЕПЕРЬ ИСПОЛЬЗУЕМ ТОКЕН
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.teacher_token.key}')

        data = {
            'lesson': self.lesson.id,
            'topic': 'Present Simple',
            'covered_material': 'Правила образования',
            'homework': 'Упр. 1-5',
            'student_progress': 'Усвоил хорошо',
            'next_lesson_plan': 'Past Simple'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class NotificationAPITests(APITestCase):
    """Тесты API для уведомлений"""

    def setUp(self):
        super().setUp()
        # 👇 СОЗДАЕМ ТОКЕН ДЛЯ УЧЕНИКА
        self.student_token = Token.objects.create(user=self.student_user)

        self.notification = Notification.objects.create(
            user=self.student_user,
            title='Тест',
            message='Сообщение',
            notification_type='system'
        )

    def test_mark_notification_read(self):
        """Тест отметки уведомления как прочитанного"""
        url = reverse('notification-mark-read', args=[self.notification.id])
        # 👇 ИСПОЛЬЗУЕМ ТОКЕН, А НЕ ПОЛЬЗОВАТЕЛЯ
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.student_token.key}')

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_all_read(self):
        """Тест отметки всех уведомлений как прочитанных"""
        Notification.objects.create(
            user=self.student_user,
            title='Еще одно',
            message='Сообщение 2',
            notification_type='system'
        )

        url = reverse('notification-mark-all-read')
        # 👇 ИСПОЛЬЗУЕМ ТОКЕН, А НЕ ПОЛЬЗОВАТЕЛЯ
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.student_token.key}')

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        unread_count = Notification.objects.filter(
            user=self.student_user,
            is_read=False
        ).count()
        self.assertEqual(unread_count, 0)