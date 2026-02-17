import os
import shutil
from datetime import datetime
from pathlib import Path

def copy_file_with_date():
    # Исходный файл (UNC путь)
    source_path = r"\\fs.alkor.ru\ЦАП\ВнешниеИсточники\СБ\Остатки\Северо-Поволжский.xlsx"
    
    # Папка назначения
    destination_dir = r"D:\Ноут\Летуаль\Остатки"
    
    # Получаем текущую дату
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Получаем имя исходного файла без расширения и с расширением
    file_name = os.path.basename(source_path)
    name_without_ext, file_ext = os.path.splitext(file_name)
    
    # Создаем новое имя файла с датой
    new_file_name = f"{name_without_ext}_{current_date}{file_ext}"
    
    # Полный путь к новому файлу
    destination_path = os.path.join(destination_dir, new_file_name)
    
    try:
        # Проверяем существование исходного файла
        if not os.path.exists(source_path):
            print(f"Ошибка: Исходный файл не найден: {source_path}")
            return
        
        # Создаем целевую директорию, если она не существует
        os.makedirs(destination_dir, exist_ok=True)
        
        # Копируем файл
        shutil.copy2(source_path, destination_path)
        
        print(f"Файл успешно скопирован:")
        print(f"Из: {source_path}")
        print(f"В: {destination_path}")
        
    except PermissionError:
        print("Ошибка: Нет прав доступа к файлу или папке.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

# Альтернативная версия с использованием pathlib
def copy_file_with_date_pathlib():
    source_path = Path(r"\\fs.alkor.ru\ЦАП\ВнешниеИсточники\СБ\Остатки\Северо-Поволжский.xlsx")
    destination_dir = Path(r"D:\Ноут\Летуаль\Остатки")
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Создаем новое имя файла
    new_file_name = f"{source_path.stem}_{current_date}{source_path.suffix}"
    destination_path = destination_dir / new_file_name
    
    try:
        if not source_path.exists():
            print(f"Ошибка: Исходный файл не найден: {source_path}")
            return
        
        destination_dir.mkdir(parents=True, exist_ok=True)
        
        # Копируем файл
        shutil.copy2(source_path, destination_path)
        
        print(f"Файл успешно скопирован:")
        print(f"Из: {source_path}")
        print(f"В: {destination_path}")
        
    except PermissionError:
        print("Ошибка: Нет прав доступа к файлу или папке.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    # Выберите один из вариантов
    print("Копирование файла с добавлением даты...")
    copy_file_with_date()  # или copy_file_with_date_pathlib()