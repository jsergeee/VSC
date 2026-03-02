from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import date, time, timedelta
from decimal import Decimal
from .models import (
    User, Teacher, Student, Subject, Lesson, LessonAttendance,
    Payment, LessonReport, Notification, UserActionLog,
    Homework, HomeworkSubmission, PaymentRequest,
    GroupLesson, GroupEnrollment, Material, StudentSubjectPrice
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