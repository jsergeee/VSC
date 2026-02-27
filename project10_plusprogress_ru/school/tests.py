from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import date, time, timedelta
from decimal import Decimal
from .models import (
    User, Teacher, Student, Subject, Lesson, LessonAttendance,
    Payment, LessonReport, Notification, UserActionLog
)

User = get_user_model()


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

        self.teacher_user = User.objects.create_user(
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