# school/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, date, timedelta
from .models import (
    User, TrialRequest, LessonReport, LessonFeedback, 
    Homework, HomeworkSubmission, ScheduleTemplate, Student, Teacher
)
from .models import (
    User, TrialRequest, LessonReport, LessonFeedback, 
    Homework, HomeworkSubmission, ScheduleTemplate, Student, Teacher,
    Lesson  # ← ЭТО НУЖНО ДОБАВИТЬ!
)

# ============================================
# ЧАСТЬ 1: ФОРМЫ АУТЕНТИФИКАЦИИ И РЕГИСТРАЦИИ
# ============================================

class UserRegistrationForm(UserCreationForm):
    """
    Форма для регистрации нового пользователя
    """
    email = forms.EmailField(
        required=True, 
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.ru'
        })
    )
    phone = forms.CharField(
        max_length=20, 
        required=True, 
        label='Телефон',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (999) 123-45-67'
        })
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES, 
        required=True, 
        label='Роль',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'patronymic',  # 👈 Фамилия, потом Имя
                  'email', 'phone', 'role', 'photo', 'password1', 'password2')
        labels = {
            'username': 'Логин',
            'first_name': 'Фамилия',  # 👈 first_name = Фамилия
            'last_name': 'Имя',  # 👈 last_name = Имя
            'patronymic': 'Отчество',
            'email': 'Email',
            'phone': 'Телефон',
            'photo': 'Фото',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите логин'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите имя'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите фамилию'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите отчество'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@mail.ru'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Подтверждение пароля'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Делаем поля обязательными
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['phone'].required = True
        
        # Добавляем подсказки
        self.fields['username'].help_text = 'Обязательно. Только буквы, цифры и @/./+/-/_'
        self.fields['password1'].help_text = 'Пароль должен содержать минимум 8 символов'
        self.fields['password2'].help_text = 'Введите тот же пароль для подтверждения'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        user.role = self.cleaned_data['role']

        if commit:
            user.save()
            
            # Создаем соответствующий профиль в зависимости от роли
            if user.role == 'student':
                Student.objects.get_or_create(user=user)
            elif user.role == 'teacher':
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
        if phone and not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValidationError('Введите корректный номер телефона')
        return phone


class UserLoginForm(forms.Form):
    """
    Форма для входа пользователя
    """
    username = forms.CharField(
        max_length=150,
        label='Имя пользователя',
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Введите имя пользователя'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Введите пароль'
        }),
        label='Пароль'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            # Дополнительная валидация при необходимости
            pass
        
        return cleaned_data


# ============================================
# ЧАСТЬ 2: ФОРМЫ ПРОФИЛЯ
# ============================================

class ProfileUpdateForm(forms.ModelForm):
    """
    Форма для обновления профиля пользователя
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'patronymic', 'email', 'phone', 'photo')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Отчество'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Телефон'}),
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
    
    def clean_phone(self):
        """Валидация телефона"""
        phone = self.cleaned_data.get('phone')
        if phone and not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValidationError('Введите корректный номер телефона')
        return phone


# ============================================
# ЧАСТЬ 3: ФОРМЫ ДЛЯ УРОКОВ И ОТЧЕТОВ
# ============================================

class LessonReportForm(forms.ModelForm):
    """
    Форма для отчета о занятии
    """
    class Meta:
        model = LessonReport
        fields = ('topic', 'covered_material', 'homework', 'student_progress', 'next_lesson_plan')
        widgets = {
            'topic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Тема занятия'
            }),
            'covered_material': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Что прошли на уроке?'
            }),
            'homework': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Домашнее задание'
            }),
            'student_progress': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Успехи и сложности ученика'
            }),
            'next_lesson_plan': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'План на следующий урок'
            }),
        }
        labels = {
            'topic': 'Тема занятия',
            'covered_material': 'Пройденный материал',
            'homework': 'Домашнее задание',
            'student_progress': 'Прогресс ученика',
            'next_lesson_plan': 'План следующего занятия',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        topic = cleaned_data.get('topic')
        covered_material = cleaned_data.get('covered_material')
        
        if not topic or not covered_material:
            raise ValidationError('Тема и пройденный материал обязательны для заполнения')
        
        return cleaned_data


class LessonFeedbackForm(forms.ModelForm):
    """Форма для оценки урока"""
    rating = forms.ChoiceField(
        choices=[(i, f'{i} ★') for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'rating-radio'}),
        label='Оценка'
    )
    
    class Meta:
        model = LessonFeedback
        fields = ['rating', 'comment', 'is_public']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
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


# ============================================
# ЧАСТЬ 4: ФОРМЫ ДЛЯ ДОМАШНИХ ЗАДАНИЙ
# ============================================

class HomeworkForm(forms.ModelForm):
    """Форма создания домашнего задания"""
    deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local', 
            'class': 'form-control'
        }),
        label='Срок сдачи'
    )
    
    class Meta:
        model = Homework
        fields = ['title', 'description', 'attachments', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название задания'
            }),
            'description': forms.Textarea(attrs={
                'rows': 5, 
                'class': 'form-control',
                'placeholder': 'Подробное описание задания'
            }),
            'attachments': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'Название задания',
            'description': 'Описание',
            'attachments': 'Файл с заданием',
        }
    
    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < timezone.now():
            raise ValidationError('Срок сдачи не может быть в прошлом')
        return deadline


class HomeworkSubmissionForm(forms.ModelForm):
    """Форма сдачи домашнего задания"""
    class Meta:
        model = HomeworkSubmission
        fields = ['answer_text', 'file']
        widgets = {
            'answer_text': forms.Textarea(attrs={
                'rows': 5, 
                'class': 'form-control', 
                'placeholder': 'Напишите ответ здесь...'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'answer_text': 'Текст ответа',
            'file': 'Прикрепить файл',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        answer_text = cleaned_data.get('answer_text')
        file = cleaned_data.get('file')
        
        if not answer_text and not file:
            raise ValidationError('Добавьте текст ответа или прикрепите файл')
        
        return cleaned_data


class HomeworkCheckForm(forms.ModelForm):
    """Форма проверки домашнего задания"""
    grade = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Оценка от 1 до 5'
        }),
        label='Оценка'
    )
    
    class Meta:
        model = HomeworkSubmission
        fields = ['grade', 'teacher_comment']
        widgets = {
            'teacher_comment': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Комментарий к проверке...'
            }),
        }
        labels = {
            'grade': 'Оценка',
            'teacher_comment': 'Комментарий учителя',
        }


# ============================================
# ЧАСТЬ 5: ФОРМЫ ДЛЯ РАСПИСАНИЯ
# ============================================

class ScheduleTemplateForm(forms.ModelForm):
    """
    Форма для шаблона расписания
    """
    class Meta:
        model = ScheduleTemplate
        fields = [
            'subject', 'format', 'start_time', 'end_time',
            'repeat_type', 'start_date', 'end_date', 'max_occurrences',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'base_cost', 'base_teacher_payment',
            'meeting_link', 'meeting_platform', 'students'
        ]
        widgets = {
            'start_time': forms.TimeInput(attrs={
                'type': 'time', 
                'class': 'form-control'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time', 
                'class': 'form-control'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'max_occurrences': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Максимальное количество занятий'
            }),
            'base_cost': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'placeholder': 'Стоимость урока'
            }),
            'base_teacher_payment': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'placeholder': 'Выплата учителю'
            }),
            'meeting_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://meet.google.com/...'
            }),
            'meeting_platform': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Google Meet, Zoom, и т.д.'
            }),
            'students': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'size': '10'
            }),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'format': forms.Select(attrs={'class': 'form-control'}),
            'repeat_type': forms.Select(attrs={'class': 'form-control'}),
            'monday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tuesday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'wednesday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'thursday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'friday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'saturday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sunday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'subject': 'Предмет',
            'format': 'Формат занятия',
            'start_time': 'Время начала',
            'end_time': 'Время окончания',
            'repeat_type': 'Тип повторения',
            'start_date': 'Дата начала',
            'end_date': 'Дата окончания',
            'max_occurrences': 'Максимальное количество занятий',
            'monday': 'Пн', 'tuesday': 'Вт', 'wednesday': 'Ср',
            'thursday': 'Чт', 'friday': 'Пт', 'saturday': 'Сб', 'sunday': 'Вс',
            'base_cost': 'Стоимость урока (для ученика)',
            'base_teacher_payment': 'Выплата учителю',
            'meeting_link': 'Ссылка на встречу',
            'meeting_platform': 'Платформа',
            'students': 'Ученики',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        repeat_type = cleaned_data.get('repeat_type')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        max_occurrences = cleaned_data.get('max_occurrences')
        
        if repeat_type == 'single':
            if not start_date:
                raise ValidationError('Для разового урока укажите дату')
        else:
            weekdays = [
                cleaned_data.get('monday'),
                cleaned_data.get('tuesday'),
                cleaned_data.get('wednesday'),
                cleaned_data.get('thursday'),
                cleaned_data.get('friday'),
                cleaned_data.get('saturday'),
                cleaned_data.get('sunday'),
            ]
            if not any(weekdays):
                raise ValidationError('Выберите хотя бы один день недели')
            
            if end_date and start_date and end_date < start_date:
                raise ValidationError('Дата окончания не может быть раньше даты начала')
            
            if max_occurrences and max_occurrences < 1:
                raise ValidationError('Количество занятий должно быть положительным')
        
        return cleaned_data


# ============================================
# ЧАСТЬ 6: НОВЫЕ ФОРМЫ ДЛЯ ФИНАНСОВ
# ============================================

class StudentDepositForm(forms.Form):
    """
    Форма для пополнения баланса учеником
    """
    amount = forms.DecimalField(
        min_value=10,
        max_value=100000,
        decimal_places=2,
        label='Сумма пополнения',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите сумму',
            'step': '0.01'
        })
    )
    description = forms.CharField(
        required=False,
        label='Назначение платежа',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пополнение счета'
        })
    )
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError('Сумма должна быть положительной')
        return amount


class TeacherPaymentRequestForm(forms.Form):
    """
    Форма для запроса выплаты учителем
    """
    amount = forms.DecimalField(
        min_value=100,
        max_value=1000000,
        decimal_places=2,
        label='Сумма к выплате',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Сумма',
            'step': '0.01'
        })
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('bank_card', 'Банковская карта'),
            ('bank_account', 'Банковский счет'),
            ('yoomoney', 'ЮMoney'),
            ('cash', 'Наличными'),
        ],
        label='Способ выплаты',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    payment_details = forms.CharField(
        label='Платёжные реквизиты',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Номер карты / счета / кошелька'
        })
    )
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError('Сумма должна быть положительной')
        return amount


class PeriodFilterForm(forms.Form):
    """
    Форма фильтрации по периоду для отчетов
    """
    date_from = forms.DateField(
        required=False,
        label='Дата с',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    date_to = forms.DateField(
        required=False,
        label='Дата по',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Устанавливаем значения по умолчанию
        today = date.today()
        self.fields['date_to'].initial = today.strftime('%Y-%m-%d')
        self.fields['date_from'].initial = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError('Дата "с" не может быть позже даты "по"')
        
        return cleaned_data


class BulkLessonCompleteForm(forms.Form):
    """
    Форма для массового завершения уроков
    """
    lesson_ids = forms.MultipleChoiceField(
        label='Выберите уроки для завершения',
        widget=forms.CheckboxSelectMultiple
    )
    topic = forms.CharField(
        max_length=200,
        label='Тема занятия',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    covered_material = forms.CharField(
        label='Пройденный материал',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    homework = forms.CharField(
        label='Домашнее задание',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    student_progress = forms.CharField(
        label='Прогресс учеников',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    def __init__(self, *args, lesson_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if lesson_choices:
            self.fields['lesson_ids'].choices = lesson_choices


# ============================================
# ЧАСТЬ 7: ФОРМЫ ДЛЯ АДМИН-ПАНЕЛИ
# ============================================

class CustomUserCreationForm(UserCreationForm):
    """
    Форма для создания пользователя в админ-панели
    """
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'patronymic',
                 'email', 'phone', 'role', 'is_active', 'is_staff')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['phone'].required = True
        
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class CustomUserChangeForm(UserChangeForm):
    """
    Форма для изменения пользователя в админ-панели
    """
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'patronymic',
                 'email', 'phone', 'photo', 'role',
                 'is_active', 'is_staff', 'is_superuser', 'is_email_verified',
                 'groups', 'user_permissions')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class AdminLessonFilterForm(forms.Form):
    """
    Форма фильтрации уроков в админке
    """
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.all(),
        required=False,
        label='Учитель',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        required=False,
        label='Ученик',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    subject = forms.ModelChoiceField(
        queryset=None,  # Будет заполнено в __init__
        required=False,
        label='Предмет',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'Все')] + list(Lesson.STATUS_CHOICES),
        required=False,
        label='Статус',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        label='Дата с',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        label='Дата по',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Subject
        self.fields['subject'].queryset = Subject.objects.all()


# ============================================
# ЧАСТЬ 8: ПРОЧИЕ ФОРМЫ
# ============================================

class TrialRequestForm(forms.ModelForm):
    """
    Форма для заявки на пробный урок
    """
    class Meta:
        model = TrialRequest
        fields = ('name', 'email', 'phone', 'subject')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control register-input-home',
                'placeholder': 'Ваше имя',
                'required': 'required'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control register-input-home',
                'placeholder': 'Адрес электронной почты',
                'required': 'required'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control register-input-home',
                'placeholder': 'Ваш телефон',
                'required': 'required'
            }),
            'subject': forms.Select(attrs={
                'class': 'form-control register-input-home',
                'required': 'required'
            }),
        }
        labels = {
            'name': 'Имя',
            'email': 'Email',
            'phone': 'Телефон',
            'subject': 'Предмет',
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValidationError('Введите корректный номер телефона')
        return phone


class ResendVerificationForm(forms.Form):
    """
    Форма для повторной отправки письма подтверждения
    """
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            # Не сообщаем, что пользователь не найден (безопасность)
            pass
        return email


class StudentNoteForm(forms.Form):
    """
    Форма для заметок учителя об ученике
    """
    note = forms.CharField(
        label='Заметка',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Введите заметку об ученике...'
        })
    )
    is_private = forms.BooleanField(
        required=False,
        label='Приватная заметка',
        help_text='Только для учителя'
    )


class MaterialFilterForm(forms.Form):
    """
    Форма фильтрации методических материалов
    """
    subject = forms.ChoiceField(
        required=False,
        label='Предмет',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    material_type = forms.ChoiceField(
        required=False,
        label='Тип материала',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    search = forms.CharField(
        required=False,
        label='Поиск',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Subject, Material
        
        subject_choices = [('', 'Все предметы')]
        subject_choices += [(s.id, s.name) for s in Subject.objects.all()]
        self.fields['subject'].choices = subject_choices
        
        type_choices = [('', 'Все типы')]
        type_choices += Material.MATERIAL_TYPES
        self.fields['material_type'].choices = type_choices