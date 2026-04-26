from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Кастомная модель пользователя. Пока пустая, но расширить легко."""
    
    def __str__(self):
        return self.username