# school/serializers.py
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import (
    User, Teacher, Student, Subject, LessonFormat, Lesson,
    LessonAttendance, LessonReport, Payment, Schedule, TrialRequest,
    Material, Deposit, StudentNote, GroupLesson, GroupEnrollment,
    Notification, LessonFeedback, TeacherRating, Homework,
    HomeworkSubmission, ScheduleTemplate, ScheduleTemplateStudent,
    StudentSubjectPrice, EmailVerificationToken, PaymentRequest
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 
                  'patronymic', 'email', 'phone', 'photo', 'role']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)


class TeacherSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    subjects = serializers.PrimaryKeyRelatedField(many=True, queryset=Subject.objects.all())
    
    class Meta:
        model = Teacher
        fields = ['id', 'user', 'subjects', 'bio', 'education', 
                  'experience', 'certificate', 'payment_details']
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        subjects = validated_data.pop('subjects', [])
        
        user_data['role'] = 'teacher'
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        
        teacher = Teacher.objects.create(user=user, **validated_data)
        teacher.subjects.set(subjects)
        return teacher


class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    teachers = serializers.PrimaryKeyRelatedField(many=True, queryset=Teacher.objects.all())
    
    class Meta:
        model = Student
        fields = ['id', 'user', 'teachers', 'parent_name', 'parent_phone', 'notes']
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        teachers = validated_data.pop('teachers', [])
        
        user_data['role'] = 'student'
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        
        student = Student.objects.create(user=user, **validated_data)
        student.teachers.set(teachers)
        return student


class LessonAttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    
    class Meta:
        model = LessonAttendance
        fields = ['id', 'student', 'student_name', 'cost', 'discount', 
                  'teacher_payment_share', 'status']


class LessonSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    attendances = LessonAttendanceSerializer(source='attendance', many=True, read_only=True)
    
    students_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=True
    )
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'teacher', 'teacher_name', 'subject', 'subject_name',
            'date', 'start_time', 'end_time', 'duration',
            'price_type', 'base_cost', 'base_teacher_payment',
            'meeting_link', 'meeting_platform', 'video_room',
            'status', 'notes', 'attendances', 'students_data'
        ]
    
    def create(self, validated_data):
        # Извлекаем students_data из validated_data
        students_data = validated_data.pop('students_data')
        
        # Создаем урок без students_data
        lesson = Lesson.objects.create(**validated_data)
        
        # Создаем записи посещаемости для каждого ученика
        for student_item in students_data:
            student = Student.objects.get(id=student_item['student_id'])
            LessonAttendance.objects.create(
                lesson=lesson,
                student=student,
                cost=student_item.get('cost', 1000),
                teacher_payment_share=student_item.get('teacher_payment', 700),
                status='registered'
            )
        
        return lesson
    
    
class SimpleLessonSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.get_full_name')
    subject_name = serializers.CharField(source='subject.name')
    students_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = ['id', 'date', 'start_time', 'end_time', 
                  'subject_name', 'teacher_name', 'status', 'students_count']
    
    def get_students_count(self, obj):
        return obj.attendance.count()
    
    
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8, label='Подтверждение пароля')
    
    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'email', 'first_name', 'last_name', 'phone']
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Пароли не совпадают")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        validated_data['role'] = 'student'  # По умолчанию ученик
        user = User.objects.create_user(**validated_data)
        return user
    
    

class HomeworkSerializer(serializers.ModelSerializer):
    """Сериализатор для домашних заданий"""
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Homework
        fields = ['id', 'title', 'description', 'attachments', 'deadline', 
                  'created_at', 'updated_at', 'is_active', 'status_display',
                  'teacher', 'teacher_name', 'student', 'student_name', 
                  'subject', 'subject_name', 'lesson']
    
    def get_status_display(self, obj):
        return obj.get_status_display()


class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    """Сериализатор для сданных заданий"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    
    class Meta:
        model = HomeworkSubmission
        fields = '__all__'


class MaterialSerializer(serializers.ModelSerializer):
    """Сериализатор для методических материалов"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Material
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    """Сериализатор для платежей"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Payment
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    """Сериализатор для уведомлений"""
    
    class Meta:
        model = Notification
        fields = '__all__'


class LessonFeedbackSerializer(serializers.ModelSerializer):
    """Сериализатор для отзывов о уроках"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    
    class Meta:
        model = LessonFeedback
        fields = '__all__'


class GroupLessonSerializer(serializers.ModelSerializer):
    """Сериализатор для групповых уроков"""
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    students_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GroupLesson
        fields = '__all__'
    
    def get_students_count(self, obj):
        return obj.enrollments.count()


class GroupEnrollmentSerializer(serializers.ModelSerializer):
    """Сериализатор для записей на групповые уроки"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    
    class Meta:
        model = GroupEnrollment
        fields = '__all__'


class ScheduleTemplateSerializer(serializers.ModelSerializer):
    """Сериализатор для шаблонов расписания"""
    
    class Meta:
        model = ScheduleTemplate
        fields = '__all__'


class StudentSubjectPriceSerializer(serializers.ModelSerializer):
    """Сериализатор для индивидуальных цен"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    
    class Meta:
        model = StudentSubjectPrice
        fields = '__all__'


class TrialRequestSerializer(serializers.ModelSerializer):
    """Сериализатор для заявок на пробный урок"""
    
    class Meta:
        model = TrialRequest
        fields = '__all__'


class DepositSerializer(serializers.ModelSerializer):
    """Сериализатор для депозитов"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    
    class Meta:
        model = Deposit
        fields = '__all__'


class StudentNoteSerializer(serializers.ModelSerializer):
    """Сериализатор для заметок об учениках"""
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    
    class Meta:
        model = StudentNote
        fields = '__all__'


class PaymentRequestSerializer(serializers.ModelSerializer):
    """Сериализатор для запросов на выплаты"""
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    
    class Meta:
        model = PaymentRequest
        fields = '__all__'


class LessonReportSerializer(serializers.ModelSerializer):
    """Сериализатор для отчетов о уроках"""
    
    class Meta:
        model = LessonReport
        fields = '__all__'