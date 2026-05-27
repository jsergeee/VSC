# task_tracker_v1.py

tasks = []  # список задач, каждая задача = словарь

def show_menu():
    print("\n=== Трекер задач ===")
    print("1. Добавить задачу")
    print("2. Показать задачи")
    print("3. Отметить задачу выполненной")
    print("4. Выход")

def add_task():
    title = input("Название задачи: ")
    tasks.append({"title": title, "done": False})
    print(f"Задача '{title}' добавлена")

def show_tasks():
    if not tasks:
        print("Нет задач")
        return
    for i, task in enumerate(tasks, 1):
        status = "✓" if task["done"] else " "
        print(f"{i}. [{status}] {task['title']}")

def mark_done():
    show_tasks()
    num = int(input("Номер задачи для отметки: ")) - 1
    if 0 <= num < len(tasks):
        tasks[num]["done"] = True
        print("Отмечено")
    else:
        print("Неверный номер")

while True:
    show_menu()
    choice = input("Выберите действие: ")
    
    if choice == "1":
        add_task()
    elif choice == "2":
        show_tasks()
    elif choice == "3":
        mark_done()
    elif choice == "4":
        print("До свидания")
        break
    else:
        print("Неверный выбор")