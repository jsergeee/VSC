# fix_balance.py
import os
import django

# Правильное имя проекта - plusprogress
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plusprogress.settings')
django.setup()

from school.models import Student, Payment, Deposit
from django.db.models import Sum

def fix_student_balance(student_id):
    """Исправляет баланс ученика"""
    try:
        student = Student.objects.get(id=student_id)
        user = student.user
        
        print(f"\n{'='*60}")
        print(f"ИСПРАВЛЕНИЕ БАЛАНСА: {user.get_full_name()} (ID: {student_id})")
        print(f"{'='*60}")
        
        # Текущий баланс
        print(f"\n1. Текущий баланс в БД: {user.balance} ₽")
        
        # Считаем все списания (уроки)
        payments = Payment.objects.filter(user=user, payment_type='expense')
        total_payments = payments.aggregate(Sum('amount'))['amount__sum'] or 0
        print(f"\n2. Списано за уроки: {total_payments} ₽")
        for p in payments:
            print(f"   - {p.created_at.strftime('%d.%m.%Y')}: {p.amount}₽ - {p.description}")
        
        # Считаем все пополнения
        incomes = Payment.objects.filter(user=user, payment_type='income')
        total_incomes = incomes.aggregate(Sum('amount'))['amount__sum'] or 0
        print(f"\n3. Пополнено: {total_incomes} ₽")
        for i in incomes:
            print(f"   - {i.created_at.strftime('%d.%m.%Y')}: {i.amount}₽ - {i.description}")
        
        # Считаем депозиты
        deposits = Deposit.objects.filter(student=student)
        total_deposits = deposits.aggregate(Sum('amount'))['amount__sum'] or 0
        if total_deposits > 0:
            print(f"\n4. Депозиты: {total_deposits} ₽")
            for d in deposits:
                print(f"   - {d.created_at.strftime('%d.%m.%Y')}: {d.amount}₽ - {d.description}")
        
        # Правильный баланс
        correct_balance = total_incomes + total_deposits - total_payments
        print(f"\n✅ Правильный баланс должен быть: {correct_balance} ₽")
        print(f"   Формула: {total_incomes} + {total_deposits} - {total_payments} = {correct_balance}")
        
        # Исправляем если нужно
        if user.balance != correct_balance:
            user.balance = correct_balance
            user.save()
            print(f"✅ Баланс ИСПРАВЛЕН на {user.balance} ₽")
        else:
            print("✅ Баланс уже правильный")
            
        print(f"\n{'='*60}")
        
    except Student.DoesNotExist:
        print(f"❌ Ученик с ID {student_id} не найден")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    # Исправляем ученика с ID 2
    fix_student_balance(2)