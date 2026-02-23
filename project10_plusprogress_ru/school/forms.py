# school/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, TrialRequest, LessonReport
from django import forms
from .models import LessonFeedback
from .models import Homework, HomeworkSubmission
from django import forms
from django.core.exceptions import ValidationError



class UserRegistrationForm(UserCreationForm):
    """
    Форма для регистрации нового пользователя
    """
    email = forms.EmailField(required=True, label='Email')
    phone = forms.CharField(max_length=20, required=True, label='Телефон')
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True, label='Роль')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'patronymic',
                 'email', 'phone', 'role', 'photo', 'password1', 'password2')
        labels = {
            'username': 'Имя пользователя',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'patronymic': 'Отчество',
            'photo': 'Фото',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем поля обязательными
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['phone'].required = True

        # Добавляем классы для стилизации
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        user.role = self.cleaned_data['role']

        if commit:
            user.save()

            # Создаем соответствующий профиль в зависимости от роли
            if user.role == 'student':
                from .models import Student
                Student.objects.get_or_create(user=user)
            elif user.role == 'teacher':
                from .models import Teacher
                Teacher.objects.get_or_create(user=user)

        return user

    def clean_email(self):
        """Проверка уникальности email"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        return email

    def clean_phone(self):
        """Проверка формата телефона"""
        phone = self.cleaned_data.get('phone')
        # Простая валидация - можно расширить
        if phone and not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValidationError('Введите корректный номер телефона')
        return phone

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Добавляем подсказки для полей
        self.fields['username'].help_text = 'Обязательно. Только буквы, цифры и @/./+/-/_'
        self.fields['password1'].help_text = 'Пароль должен содержать минимум 8 символов'
        self.fields['password2'].help_text = 'Введите тот же пароль для подтверждения'

        # Делаем поля обязательными
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['phone'].required = True

        # Добавляем плейсхолдеры
        self.fields['first_name'].widget.attrs['placeholder'] = 'Введите имя'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Введите фамилию'
        self.fields['email'].widget.attrs['placeholder'] = 'example@mail.ru'
        self.fields['phone'].widget.attrs['placeholder'] = '+7 (999) 123-45-67'


class UserLoginForm(forms.Form):
    """
    Форма для входа пользователя
    """
    username = forms.CharField(
        max_length=150,
        label='Имя пользователя',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите имя пользователя'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'}),
        label='Пароль'
    )


class TrialRequestForm(forms.ModelForm):
    """
    Форма для заявки на пробный урок
    """
    class Meta:
        model = TrialRequest
        fields = ('name', 'email', 'phone', 'subject')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'register-input-home',
                'placeholder': 'Ваше имя',
                'required': 'required'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'register-input-home',
                'placeholder': 'Адрес электронной почты',
                'required': 'required'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'register-input-home',
                'placeholder': 'Ваш телефон',
                'required': 'required'
            }),
            'subject': forms.Select(attrs={
                'class': 'register-input-home',
                'required': 'required'
            }),
        }
        labels = {
            'name': 'Имя',
            'email': 'Email',
            'phone': 'Телефон',
            'subject': 'Предмет',
        }


class LessonReportForm(forms.ModelForm):
    """
    Форма для отчета о занятии
    """
    class Meta:
        model = LessonReport
        fields = ('topic', 'covered_material', 'homework', 'student_progress', 'next_lesson_plan')
        widgets = {
            'topic': forms.TextInput(attrs={'class': 'form-control'}),
            'covered_material': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'homework': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'student_progress': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'next_lesson_plan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'topic': 'Тема занятия',
            'covered_material': 'Пройденный материал',
            'homework': 'Домашнее задание',
            'student_progress': 'Прогресс ученика',
            'next_lesson_plan': 'План следующего занятия',
        }


class ProfileUpdateForm(forms.ModelForm):
    """
    Форма для обновления профиля пользователя
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'patronymic', 'email', 'phone', 'photo')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'patronymic': 'Отчество',
            'email': 'Email',
            'phone': 'Телефон',
            'photo': 'Фото',
        }


class CustomUserCreationForm(UserCreationForm):
    """
    Форма для создания пользователя в админ-панели
    """
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'patronymic',
                 'email', 'phone', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['phone'].required = True


class CustomUserChangeForm(UserChangeForm):
    """
    Форма для изменения пользователя в админ-панели
    """
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'patronymic',
                 'email', 'phone', 'photo', 'role', 'balance',
                 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')




class LessonFeedbackForm(forms.ModelForm):
    """Форма для оценки урока"""
    class Meta:
        model = LessonFeedback
        fields = ['rating', 'comment', 'is_public']
        widgets = {
            'rating': forms.RadioSelect(choices=LessonFeedback.RATING_CHOICES),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Расскажите, как прошёл урок. Что понравилось? Что можно улучшить?'
            }),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'rating': 'Оцените урок',
            'comment': 'Ваш отзыв',
            'is_public': 'Разрешить публикацию отзыва на сайте',
        }
        help_texts = {
            'is_public': 'Если отметить, ваш отзыв может быть опубликован на сайте школы',
        }


class HomeworkForm(forms.ModelForm):
    """Форма создания домашнего задания"""
    class Meta:
        model = Homework
        fields = ['title', 'description', 'attachments', 'deadline']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Название задания',
            'description': 'Описание',
            'attachments': 'Файл с заданием',
            'deadline': 'Срок сдачи',
        }

class HomeworkSubmissionForm(forms.ModelForm):
    """Форма сдачи домашнего задания"""
    class Meta:
        model = HomeworkSubmission
        fields = ['answer_text', 'file']
        widgets = {
            'answer_text': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Напишите ответ здесь...'}),
        }
        labels = {
            'answer_text': 'Текст ответа',
            'file': 'Прикрепить файл',
        }

class HomeworkCheckForm(forms.ModelForm):
    """Форма проверки домашнего задания"""
    class Meta:
        model = HomeworkSubmission
        fields = ['grade', 'teacher_comment']
        widgets = {
            'teacher_comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'grade': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }
        labels = {
            'grade': 'Оценка',
            'teacher_comment': 'Комментарий учителя',
        }


from .models import ScheduleTemplate

class ScheduleTemplateForm(forms.ModelForm):
    class Meta:
        model = ScheduleTemplate
        fields = [
            'subject', 'format', 'start_time', 'end_time',
            'repeat_type', 'start_date', 'end_date', 'max_occurrences',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'price_type', 'base_cost', 'base_teacher_payment',
            'meeting_link', 'meeting_platform', 'students'
        ]
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'max_occurrences': forms.NumberInput(attrs={'class': 'form-control'}),
            'base_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'base_teacher_payment': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'meeting_link': forms.URLInput(attrs={'class': 'form-control'}),
            'meeting_platform': forms.TextInput(attrs={'class': 'form-control'}),
        }