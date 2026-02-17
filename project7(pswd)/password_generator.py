import random
import string
import secrets
import argparse
from typing import List

class PasswordGenerator:
    def __init__(self):
        # Категории символов
        self.lowercase = string.ascii_lowercase
        self.uppercase = string.ascii_uppercase
        self.digits = string.digits
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # Полный набор символов
        self.all_chars = self.lowercase + self.uppercase + self.digits + self.special_chars
    
    def generate_password(self, 
                         min_length: int = 12, 
                         max_length: int = 20,
                         use_lowercase: bool = True,
                         use_uppercase: bool = True,
                         use_digits: bool = True,
                         use_special: bool = True) -> str:
        """
        Генерация случайного пароля с заданными параметрами
        
        Args:
            min_length: минимальная длина пароля
            max_length: максимальная длина пароля
            use_lowercase: использовать строчные буквы
            use_uppercase: использовать заглавные буквы
            use_digits: использовать цифры
            use_special: использовать специальные символы
        
        Returns:
            Сгенерированный пароль
        """
        
        # Проверка параметров
        if min_length < 4:
            raise ValueError("Минимальная длина пароля должна быть не менее 4 символов")
        
        if max_length < min_length:
            raise ValueError("Максимальная длина должна быть больше или равна минимальной")
        
        # Выбор случайной длины в заданном диапазоне
        length = random.randint(min_length, max_length)
        
        # Сбор выбранных категорий символов
        char_pool = ""
        char_categories = []
        
        if use_lowercase:
            char_pool += self.lowercase
            char_categories.append(self.lowercase)
        if use_uppercase:
            char_pool += self.uppercase
            char_categories.append(self.uppercase)
        if use_digits:
            char_pool += self.digits
            char_categories.append(self.digits)
        if use_special:
            char_pool += self.special_chars
            char_categories.append(self.special_chars)
        
        if not char_pool:
            raise ValueError("Должен быть выбран хотя бы один тип символов")
        
        # Генерация пароля с гарантированным включением хотя бы одного символа из каждой категории
        password_chars = []
        
        # Гарантируем наличие хотя бы одного символа из каждой выбранной категории
        for category in char_categories:
            password_chars.append(secrets.choice(category))
        
        # Заполняем оставшуюся длину случайными символами из общего пула
        remaining_length = length - len(password_chars)
        password_chars.extend(secrets.choice(char_pool) for _ in range(remaining_length))
        
        # Перемешиваем символы для случайного порядка
        random.shuffle(password_chars)
        
        return ''.join(password_chars)
    
    def generate_multiple_passwords(self, 
                                   count: int = 5,
                                   min_length: int = 12,
                                   max_length: int = 20,
                                   **kwargs) -> List[str]:
        """
        Генерация нескольких паролей
        
        Args:
            count: количество паролей для генерации
            min_length: минимальная длина пароля
            max_length: максимальная длина пароля
            **kwargs: дополнительные параметры для generate_password
        
        Returns:
            Список сгенерированных паролей
        """
        passwords = []
        for _ in range(count):
            password = self.generate_password(min_length, max_length, **kwargs)
            passwords.append(password)
        return passwords
    
    def assess_password_strength(self, password: str) -> dict:
        """
        Оценка надежности пароля
        
        Args:
            password: пароль для оценки
        
        Returns:
            Словарь с оценкой надежности
        """
        score = 0
        feedback = []
        
        # Критерии оценки
        length = len(password)
        
        if length >= 12:
            score += 2
        elif length >= 8:
            score += 1
        else:
            feedback.append("Слишком короткий пароль")
        
        # Проверка наличия разных типов символов
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in self.special_chars for c in password)
        
        if has_lower:
            score += 1
        if has_upper:
            score += 1
        if has_digit:
            score += 1
        if has_special:
            score += 1
        
        # Определение уровня надежности
        if score >= 6:
            strength = "Очень надежный"
        elif score >= 4:
            strength = "Надежный"
        elif score >= 2:
            strength = "Средний"
        else:
            strength = "Слабый"
        
        return {
            'score': score,
            'strength': strength,
            'length': length,
            'has_lowercase': has_lower,
            'has_uppercase': has_upper,
            'has_digits': has_digit,
            'has_special': has_special,
            'feedback': feedback
        }


def main():
    parser = argparse.ArgumentParser(description='Генератор сложных паролей')
    parser.add_argument('-n', '--number', type=int, default=5, 
                       help='Количество паролей для генерации (по умолчанию: 5)')
    parser.add_argument('--min-length', type=int, default=12,
                       help='Минимальная длина пароля (по умолчанию: 12)')
    parser.add_argument('--max-length', type=int, default=20,
                       help='Максимальная длина пароля (по умолчанию: 20)')
    parser.add_argument('--no-lowercase', action='store_true',
                       help='Не использовать строчные буквы')
    parser.add_argument('--no-uppercase', action='store_true',
                       help='Не использовать заглавные буквы')
    parser.add_argument('--no-digits', action='store_true',
                       help='Не использовать цифры')
    parser.add_argument('--no-special', action='store_true',
                       help='Не использовать специальные символы')
    parser.add_argument('--assess', action='store_true',
                       help='Показать оценку надежности для каждого пароля')
    
    args = parser.parse_args()
    
    # Создание генератора
    generator = PasswordGenerator()
    
    try:
        # Генерация паролей
        passwords = generator.generate_multiple_passwords(
            count=args.number,
            min_length=args.min_length,
            max_length=args.max_length,
            use_lowercase=not args.no_lowercase,
            use_uppercase=not args.no_uppercase,
            use_digits=not args.no_digits,
            use_special=not args.no_special
        )
        
        # Вывод паролей
        print(f"\nСгенерировано {len(passwords)} паролей:")
        print("-" * 50)
        
        for i, password in enumerate(passwords, 1):
            print(f"{i:2}. {password}")
            
            if args.assess:
                assessment = generator.assess_password_strength(password)
                print(f"    Длина: {assessment['length']}, "
                      f"Надежность: {assessment['strength']}")
                if assessment['feedback']:
                    print(f"    Замечания: {', '.join(assessment['feedback'])}")
                print()
        
        print("-" * 50)
        
        # Пример использования с разными настройками
        print("\nПримеры паролей с разными настройками:")
        
        # Короткий, но сложный пароль
        short_strong = generator.generate_password(min_length=8, max_length=10)
        print(f"Короткий сложный: {short_strong}")
        
        # Длинный пароль только из букв
        long_letters = generator.generate_password(
            min_length=15, max_length=20,
            use_digits=False, use_special=False
        )
        print(f"Длинный буквенный: {long_letters}")
        
        # Пароль только из цифр и специальных символов
        numeric_special = generator.generate_password(
            min_length=10, max_length=12,
            use_lowercase=False, use_uppercase=False
        )
        print(f"Цифры и спецсимволы: {numeric_special}")
        
    except ValueError as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()