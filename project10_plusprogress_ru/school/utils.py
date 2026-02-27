import logging
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
import smtplib

logger = logging.getLogger(__name__)


def send_verification_email(user, request):
    """Отправляет письмо с подтверждением email"""
    try:
        from .models import EmailVerificationToken

        print(f"\n📧 Создаем токен для {user.email}")

        # Создаем или обновляем токен
        EmailVerificationToken.objects.filter(user=user).delete()
        print(f"   Старые токены удалены")

        token = EmailVerificationToken.objects.create(user=user)
        print(f"   Новый токен создан: {token.token}")
        print(f"   Истекает: {token.expires_at}")

        # Формируем ссылку для подтверждения
        verification_url = request.build_absolute_uri(
            reverse('verify_email', args=[str(token.token)])
        )
        print(f"   Ссылка: {verification_url}")

        # Контекст для письма
        context = {
            'user': user,
            'verification_url': verification_url,
            'site_name': 'Плюс Прогресс',
            'valid_hours': 48,
            'support_email': settings.DEFAULT_FROM_EMAIL,
        }

        # Рендерим HTML письмо
        html_message = render_to_string(
            'emails/email_verification.html',
            context
        )
        plain_message = strip_tags(html_message)

        # Проверяем настройки email
        if settings.DEBUG:
            print(f"📧 Режим отладки - письмо будет выведено в консоль")
            print(f"📧 Ссылка для подтверждения: {verification_url}")

        # Отправляем письмо
        send_mail(
            subject='Подтверждение email - Плюс Прогресс',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        # Обновляем время отправки
        user.email_verification_sent = timezone.now()
        user.save(update_fields=['email_verification_sent'])

        print(f"✅ Письмо подтверждения отправлено на {user.email}")
        logger.info(f"Письмо подтверждения отправлено на {user.email}")
        return True

    except (BadHeaderError, smtplib.SMTPException) as e:
        print(f"❌ SMTP ошибка: {e}")
        logger.error(f"SMTP ошибка при отправке письма: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка при отправке письма: {e}")
        logger.error(f"Неожиданная ошибка при отправке письма: {e}")
        return False


def send_verification_success_email(user):
    """Отправляет письмо об успешном подтверждении"""
    try:
        print(f"📧 Отправляем письмо об успехе на {user.email}")

        context = {
            'user': user,
            'site_name': 'Плюс Прогресс',
            'login_url': 'http://127.0.0.1:8000/login/',
        }

        html_message = render_to_string(
            'emails/email_verified.html',
            context
        )
        plain_message = strip_tags(html_message)

        send_mail(
            subject='Email подтвержден - Плюс Прогресс',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        print(f"✅ Письмо об успехе отправлено")
        return True

    except Exception as e:
        print(f"⚠️ Ошибка отправки письма об успехе: {e}")
        logger.error(f"Ошибка отправки письма об успехе: {e}")
        return False


def send_verification_success_email(user):
    """Отправляет письмо об успешном подтверждении"""
    try:
        context = {
            'user': user,
            'site_name': 'Плюс Прогресс',
        }

        html_message = render_to_string(
            'emails/email_verified.html',
            context
        )
        plain_message = strip_tags(html_message)

        send_mail(
            subject='Email подтвержден - Плюс Прогресс',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки письма об успехе: {e}")
        return False


# school/utils.py - добавьте функции логирования
from .models import UserActionLog


def log_user_action(request, action_type, description, object_id=None, object_type='', additional_data=None):
    """
    Логирование действия пользователя
    """
    print(f"\n🔍 ПОПЫТКА ЛОГИРОВАНИЯ:")
    print(f"   action_type: {action_type}")
    print(f"   description: {description}")
    print(f"   user: {request.user}")
    print(f"   authenticated: {request.user.is_authenticated}")

    if not request.user.is_authenticated:
        print("❌ Пользователь не аутентифицирован")
        return None

    # Получаем IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    print(f"✅ Создаем запись в БД...")

    try:
        log = UserActionLog.objects.create(
            user=request.user,
            action_type=action_type,
            description=description,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            url=request.build_absolute_uri(),
            object_id=object_id,
            object_type=object_type or '',
            additional_data=additional_data or {}
        )
        print(f"✅ Лог создан! ID: {log.id}")
        return log
    except Exception as e:
        print(f"❌ ОШИБКА при создании лога: {e}")
        return None