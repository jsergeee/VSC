# school/management/commands/check_balances.py
from django.core.management.base import BaseCommand
from django.db.models import Sum
from school.models import User, Student, Payment, LessonAttendance
from datetime import datetime

class Command(BaseCommand):
    help = 'Проверяет соответствие балансов в БД и расчетных балансов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Исправлять расхождения (обновлять user.balance)',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Проверить конкретного пользователя (username)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('🔍 ПРОВЕРКА БАЛАНСОВ УЧЕНИКОВ'))
        self.stdout.write(self.style.SUCCESS(f'📅 {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # Получаем учеников для проверки
        if options['user']:
            users = User.objects.filter(username=options['user'], role='student')
            if not users.exists():
                self.stdout.write(self.style.ERROR(f'❌ Пользователь {options["user"]} не найден'))
                return
        else:
            users = User.objects.filter(role='student')

        total_checked = 0
        total_fixed = 0
        total_errors = 0

        for user in users:
            if not hasattr(user, 'student_profile'):
                continue

            student = user.student_profile
            total_checked += 1

            # Расчетный баланс
            total_deposits = Payment.objects.filter(
                user=user,
                payment_type='income'
            ).aggregate(Sum('amount'))['amount__sum'] or 0

            attended_cost = LessonAttendance.objects.filter(
                student=student,
                status='attended'
            ).aggregate(Sum('cost'))['cost__sum'] or 0

            calculated_balance = float(total_deposits - attended_cost)
            db_balance = float(user.balance)

            # Проверяем соответствие
            if abs(db_balance - calculated_balance) < 0.01:  # Допустимая погрешность
                self.stdout.write(
                    f'✅ {user.username:<20} {user.get_full_name():<30} '
                    f'БД: {db_balance:8.2f} ₽ = Расчет: {calculated_balance:8.2f} ₽'
                )
            else:
                total_errors += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ {user.username:<20} {user.get_full_name():<30} '
                        f'БД: {db_balance:8.2f} ₽ ≠ Расчет: {calculated_balance:8.2f} ₽'
                    )
                )

                # Если нужно исправить
                if options['fix']:
                    old_balance = user.balance
                    user.balance = calculated_balance
                    user.save()
                    total_fixed += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'   ➡️ Исправлено: {old_balance:8.2f} ₽ → {calculated_balance:8.2f} ₽'
                        )
                    )

        # Итоги
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'📊 Проверено учеников: {total_checked}')
        self.stdout.write(f'⚠️  Расхождений: {total_errors}')
        if options['fix']:
            self.stdout.write(f'✅ Исправлено: {total_fixed}')
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # Рекомендация для cron
        self.stdout.write('\n💡 Для автоматической проверки добавьте в cron:')
        self.stdout.write('   0 * * * * cd /путь/к/проекту && python manage.py check_balances')