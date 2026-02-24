## 📊 РЕЗЮМЕ ПО НОВОМУ КОДУ - ВСЕ ПЕРЕМЕННЫЕ С ГРУППИРОВКОЙ

### ГРУППА 1: LessonFinanceCalculator (ФИНАНСЫ УРОКА)

python

```
calculator = LessonFinanceCalculator(lesson)
stats = calculator.stats  # Содержит:

{
    # Денежные показатели
    'total_cost': float,           # Общая стоимость урока
    'teacher_payment': float,      # Выплата учителю
    'attended_cost': float,        # Стоимость присутствовавших
    'attended_payment': float,     # Выплата за присутствовавших
    'debt_cost': float,            # Стоимость уроков в долг
    
    # Количественные показатели
    'students_total': int,         # Всего учеников
    'students_attended': int,      # Присутствовало
    'students_debt': int,          # В долг
    'students_absent': int,        # Отсутствовало
    'students_registered': int,    # Зарегистрировано
}

# Детализация по ученикам
calculator.get_attendance_details() -> [
    {
        'student_id': int,
        'student_name': str,
        'cost': float,
        'teacher_payment': float,
        'status': str,
        'balance_before': float,
        'balance_after': float
    }
]
```



### ГРУППА 2: PeriodFinanceCalculator (ФИНАНСЫ ЗА ПЕРИОД)

python

```
period_calc = PeriodFinanceCalculator(lessons, payments)

# Статистика по урокам
period_calc.lessons_stats -> {
    'total': int,                  # Всего уроков
    'completed': int,              # Проведено
    'cancelled': int,               # Отменено
    'overdue': int,                 # Просрочено
    'scheduled': int,               # Запланировано
    'total_cost': float,            # Общая стоимость
    'teacher_payment': float,       # Выплаты учителям
}

# Статистика по платежам
period_calc.payments_stats -> {
    'income': float,                # Пополнения
    'expense': float,               # Расходы учеников
    'teacher_payments': float,       # Выплаты учителям
    'total': float,                  # Всего платежей
    'count': int,                    # Количество платежей
}

# Финансы школы
period_calc.school_finances -> {
    'income': float,                 # Доход (расходы учеников)
    'expense': float,                 # Расход (выплаты учителям)
    'profit': float,                   # Прибыль
    'profit_margin': float,            # Рентабельность %
}

# Ежедневная статистика
period_calc.get_daily_stats(start, end) -> [
    {
        'date': str,
        'lessons': {...},            # lessons_stats за день
        'payments': {...},            # payments_stats за день
        'profit': float                # Прибыль за день
    }
]
```



### ГРУППА 3: StudentFinanceHelper (ФИНАНСЫ УЧЕНИКА)

python

```
student_finance = StudentFinanceHelper(student)

# Основные показатели
student_finance.balance              # Текущий баланс
student_finance.debt                  # Сумма долга
student_finance.positive_balance      # Положительный баланс

# Статистика по урокам
student_finance.get_lessons_stats(days=30) -> {
    'period_days': int,                # Период в днях
    'total': int,                       # Всего уроков
    'attended': int,                    # Посещено
    'debt': int,                         # В долг
    'total_cost': float,                  # Потрачено всего
    'average_cost': float                  # Средняя стоимость
}
```



### ГРУППА 4: TeacherFinanceHelper (ФИНАНСЫ УЧИТЕЛЯ)

python

```
teacher_finance = TeacherFinanceHelper(teacher)

# Основные показатели
teacher_finance.wallet_balance         # Баланс кошелька

# Статистика выплат
teacher_finance.get_payment_stats(days=30) -> {
    'period_days': int,                # Период в днях
    'total': float,                      # Всего выплачено
    'count': int,                         # Количество выплат
    'average': float                       # Средняя выплата
}
```



### ГРУППА 5: УНИФИЦИРОВАННЫЕ КОНТЕКСТНЫЕ ПЕРЕМЕННЫЕ

**В student_dashboard:**

python

```
context['finance'] = {
    'balance': float,
    'debt': float,
    'positive_balance': float,
    'stats': {...}  # результаты get_lessons_stats()
}
```



**В teacher_dashboard:**

python

```
context['finance'] = {
    'wallet_balance': float,
    'payment_stats': {...}  # результаты get_payment_stats()
}
```



**В teacher_lesson_detail:**

python

```
context['finance'] = {
    'total_cost': float,
    'teacher_payment': float,
    'attended_cost': float,
    'attended_payment': float,
    'debt_cost': float,
    'students_total': int,
    'students_attended': int,
    'students_debt': int
}
```



**В lesson_detail (для ученика):**

python

```
context['finance'] = {
    'student_cost': float,      # Стоимость для этого ученика
    'total_cost': float,         # Общая стоимость урока
    'students_total': int         # Всего учеников
}
```



## ✅ ПРЕИМУЩЕСТВА РЕФАКТОРИНГА

1. **Единый источник правды** - все финансовые расчеты через helper-классы
2. **Нет дублирования кода** - одна логика расчета везде
3. **Унифицированные имена** - одинаковые переменные в разных views
4. **Легкая поддержка** - изменения только в одном месте
5. **Тестируемость** - можно легко тестировать каждый helper
6. **Расширяемость** - легко добавить новые показатели
7. **Прозрачность** - четкая группировка переменных по назначению