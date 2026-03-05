# reset_balances.py
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plusprogress.settings')
django.setup()

from school.models import User, Student, Teacher, Payment, Deposit, LessonAttendance
from django.db.models import Sum

def reset_all_balances():
    """Полный пересчет всех балансов"""
    print(f"\n{'='*60}")
    print("🔄 ПЕРЕСЧЕТ ВСЕХ БАЛАНСОВ")
    print(f"{'='*60}")
    
    # 1. СБРАСЫВАЕМ ВСЕ БАЛАНСЫ В НОЛЬ
    print("\n1. Сброс балансов...")
    User.objects.update(balance=Decimal('0'))
    Teacher.objects.update(wallet_balance=Decimal('0'))
    print("   ✅ Все балансы обнулены")
    
    # 2. СЧИТАЕМ ВСЕ ПОПОЛНЕНИЯ (income)
    print("\n2. Учитываем пополнения...")
    incomes = Payment.objects.filter(payment_type='income')
    for payment in incomes:
        payment.user.balance += payment.amount
        payment.user.save()
        print(f"   +{payment.amount}₽ пользователю {payment.user.username}")
    
    # 3. СЧИТАЕМ ВСЕ СПИСАНИЯ (expense)
    print("\n3. Учитываем списания...")
    expenses = Payment.objects.filter(payment_type='expense')
    for payment in expenses:
        payment.user.balance -= payment.amount
        payment.user.save()
        print(f"   -{payment.amount}₽ пользователю {payment.user.username}")
    
    # 4. СЧИТАЕМ ВСЕ ДЕПОЗИТЫ (отдельно)
    print("\n4. Учитываем депозиты...")
    deposits = Deposit.objects.all()
    for deposit in deposits:
        deposit.student.user.balance += deposit.amount
        deposit.student.user.save()
        print(f"   +{deposit.amount}₽ ученику {deposit.student.user.username}")
    
    # 5. СЧИТАЕМ ВСЕ ПОСЕЩЕНИЯ (attended) - дополнительная проверка
    print("\n5. Проверка посещений...")
    attendances = LessonAttendance.objects.filter(status='attended')
    for att in attendances:
        # Проверяем, есть ли платеж за это посещение
        payment_exists = Payment.objects.filter(
            user=att.student.user,
            lesson=att.lesson,
            payment_type='expense'
        ).exists()
        
        if not payment_exists:
            print(f"   ⚠️ Посещение без платежа: {att.student.user.username} - {att.lesson.date} - {att.cost}₽")
            att.student.user.balance -= att.cost
            att.student.user.save()
            print(f"      ➖ Списано {att.cost}₽ (создан платеж)")
            
            # Создаем платеж
            Payment.objects.create(
                user=att.student.user,
                amount=att.cost,
                payment_type='expense',
                description=f'Автоисправление: урок {att.lesson.date}',
                lesson=att.lesson
            )
    
    # 6. СЧИТАЕМ ВЫПЛАТЫ УЧИТЕЛЯМ
    print("\n6. Пересчет выплат учителям...")
    teacher_payments = Payment.objects.filter(payment_type='teacher_payment')
    for payment in teacher_payments:
        teacher = payment.user.teacher_profile
        teacher.wallet_balance += payment.amount
        teacher.save()
        print(f"   +{payment.amount}₽ учителю {payment.user.username}")
    
    # 7. ИТОГОВАЯ ПРОВЕРКА
    print(f"\n{'='*60}")
    print("📊 ИТОГОВЫЕ БАЛАНСЫ:")
    print(f"{'='*60}")
    
    users = User.objects.all().order_by('username')
    for user in users:
        print(f"\n👤 {user.username} ({user.get_full_name()}):")
        print(f"   Баланс: {user.balance}₽")
        
        if hasattr(user, 'teacher_profile'):
            print(f"   Кошелек учителя: {user.teacher_profile.wallet_balance}₽")
        
        # Показываем платежи пользователя
        payments = Payment.objects.filter(user=user).order_by('-created_at')[:5]
        if payments:
            print(f"   Последние платежи:")
            for p in payments:
                print(f"      - {p.created_at.strftime('%d.%m.%Y')}: {p.amount}₽ ({p.payment_type})")
    
    print(f"\n{'='*60}")
    print("✅ ПЕРЕСЧЕТ ЗАВЕРШЕН")
    print(f"{'='*60}")

def reset_specific_student(student_id):
    """Сброс баланса конкретного ученика"""
    try:
        student = Student.objects.get(id=student_id)
        user = student.user
        
        print(f"\n{'='*60}")
        print(f"🔄 СБРОС БАЛАНСА УЧЕНИКА: {user.get_full_name()} (ID: {student_id})")
        print(f"{'='*60}")
        
        # Сбрасываем баланс
        old_balance = user.balance
        user.balance = Decimal('0')
        user.save()
        print(f"1. Старый баланс: {old_balance}₽")
        print(f"2. Новый баланс: {user.balance}₽")
        
        # Показываем все платежи
        payments = Payment.objects.filter(user=user).order_by('-created_at')
        print(f"\n3. Все платежи ({payments.count()}):")
        total_income = 0
        total_expense = 0
        
        for p in payments:
            if p.payment_type == 'income':
                total_income += p.amount
                print(f"   + {p.amount}₽ - {p.description} ({p.created_at.strftime('%d.%m.%Y')})")
            elif p.payment_type == 'expense':
                total_expense += p.amount
                print(f"   - {p.amount}₽ - {p.description} ({p.created_at.strftime('%d.%m.%Y')})")
        
        print(f"\n4. Статистика:")
        print(f"   Всего пополнений: {total_income}₽")
        print(f"   Всего списаний: {total_expense}₽")
        print(f"   Должно быть: {total_income - total_expense}₽")
        
        # Предлагаем исправить
        correct_balance = total_income - total_expense
        if correct_balance != 0:
            user.balance = correct_balance
            user.save()
            print(f"\n5. Баланс исправлен на {correct_balance}₽")
        
        print(f"\n{'='*60}")
        
    except Student.DoesNotExist:
        print(f"❌ Ученик с ID {student_id} не найден")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'student':
        # Сброс конкретного ученика: python reset_balances.py student 2
        if len(sys.argv) > 2:
            reset_specific_student(int(sys.argv[2]))
        else:
            print("Укажите ID ученика: python reset_balances.py student 2")
    else:
        # Полный пересчет
        print("⚠️  ВНИМАНИЕ! Этот скрипт пересчитает ВСЕ балансы!")
        print("Нажмите Ctrl+C для отмены или Enter для продолжения...")
        input()
        
        reset_all_balances()
        