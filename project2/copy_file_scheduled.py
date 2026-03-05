import os
import shutil
from datetime import datetime
import time
import sys

class FileCopier:
    """Класс для копирования файла из сетевой папки"""
    
    def __init__(self):
        # Настройки (можно вынести в конфиг файл)
        self.settings = {
            'username': r'alkor\yakovenko',
            'password': 'KtnefkmRfpfym+4',  # ← Замените на ваш пароль
            'source': r'\\fs.alkor.ru\ЦАП\ВнешниеИсточники\СБ\Остатки\Северо-Поволжский.xlsx',
            'dest_dir': r'D:\Ноут\Летуаль\Остатки',
            'log_dir': r'D:\VSC\project2\logs'
        }
        
        # Создаем папки для логов
        os.makedirs(self.settings['log_dir'], exist_ok=True)
        
    def setup_logging(self):
        """Настройка логирования"""
        log_file = os.path.join(
            self.settings['log_dir'], 
            f"copy_{datetime.now().strftime('%Y-%m-%d')}.log"
        )
        
        # Простое логирование в файл
        self.log_file = log_file
        
    def log_message(self, message):
        """Запись сообщения в лог"""
        timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        # Вывод в консоль
        print(message)
        
        # Запись в файл
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def connect_to_network(self):
        """Подключение к сетевой папке"""
        try:
            import win32wnet
            
            self.log_message("🔌 Подключение к сетевой папке...")
            
            net = win32wnet.NETRESOURCE()
            net.lpRemoteName = os.path.dirname(self.settings['source'])
            net.dwType = 1  # RESOURCETYPE_DISK
            
            win32wnet.WNetAddConnection2(
                net, 
                self.settings['password'], 
                self.settings['username'], 
                0  # CONNECT_TEMPORARY
            )
            
            self.log_message("   ✅ Подключение установлено")
            time.sleep(2)  # Ждем стабилизации
            
            return True
            
        except Exception as e:
            self.log_message(f"   ❌ Ошибка подключения: {e}")
            return False
    
    def disconnect_from_network(self):
        """Отключение от сетевой папки"""
        try:
            import win32wnet
            win32wnet.WNetCancelConnection2(
                os.path.dirname(self.settings['source']), 
                0, 
                True
            )
            self.log_message("   ✅ Подключение закрыто")
        except:
            self.log_message("   ⚠️  Не удалось корректно закрыть подключение")
    
    def check_existing_file(self):
        """Проверка, не скопирован ли уже файл сегодня"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        dest_file = f"Северо-Поволжский_{date_str}.xlsx"
        dest_path = os.path.join(self.settings['dest_dir'], dest_file)
        
        if os.path.exists(dest_path):
            try:
                size = os.path.getsize(dest_path)
                self.log_message(f"⚠️  Файл уже существует: {dest_file}")
                self.log_message(f"   Размер: {size:,} байт")
                return True, dest_path
            except:
                pass
                
        return False, dest_path
    
    def copy_file(self):
        """Основная функция копирования"""
        self.setup_logging()
        
        self.log_message("=" * 60)
        self.log_message(f"🚀 ЗАПУСК СКРИПТА: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        self.log_message("=" * 60)
        
        # Проверяем существование файла
        already_exists, dest_path = self.check_existing_file()
        if already_exists:
            self.log_message("✅ Задача уже выполнена сегодня")
            return True
        
        self.log_message(f"📁 Источник: {self.settings['source']}")
        self.log_message(f"💾 Назначение: {dest_path}")
        
        # Подключаемся к сети
        if not self.connect_to_network():
            return False
        
        # Пробуем скопировать файл
        success = False
        
        try:
            # Создаем папку назначения
            os.makedirs(self.settings['dest_dir'], exist_ok=True)
            
            # Метод 1: Стандартное копирование
            self.log_message("\n📤 Копирование файла...")
            shutil.copy2(self.settings['source'], dest_path)
            
            # Проверяем результат
            if os.path.exists(dest_path):
                dest_size = os.path.getsize(dest_path)
                if dest_size > 0:
                    self.log_message(f"   ✅ Файл успешно скопирован!")
                    self.log_message(f"   📊 Размер: {dest_size:,} байт ({dest_size/1024/1024:.1f} MB)")
                    success = True
                else:
                    self.log_message("   ⚠️  Файл создан, но имеет размер 0 байт")
            else:
                self.log_message("   ❌ Файл не был создан")
                
        except PermissionError as e:
            self.log_message(f"   ❌ Ошибка доступа: {e}")
            self.log_message("   ⚠️  Возможно файл заблокирован (открыт в Excel)")
            
        except Exception as e:
            self.log_message(f"   ❌ Ошибка копирования: {e}")
            
            # Пробуем альтернативный метод
            try:
                self.log_message("   🔄 Пробуем альтернативный метод...")
                with open(self.settings['source'], 'rb') as src, open(dest_path, 'wb') as dst:
                    data = src.read()
                    dst.write(data)
                
                if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
                    self.log_message("   ✅ Альтернативный метод сработал!")
                    success = True
            except Exception as e2:
                self.log_message(f"   ❌ Альтернативный метод также не сработал: {e2}")
        
        finally:
            # Всегда отключаемся от сети
            self.disconnect_from_network()
        
        # Итог
        self.log_message("\n" + "=" * 60)
        if success:
            self.log_message("🎉 ОПЕРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
            self.log_message(f"📁 Файл сохранен: {os.path.basename(dest_path)}")
            self.log_message(f"📂 Папка: {self.settings['dest_dir']}")
        else:
            self.log_message("❌ ОПЕРАЦИЯ НЕ УДАЛАСЯ")
            self.log_message("📋 Проверьте:")
            self.log_message("   1. Доступность сетевой папки")
            self.log_message("   2. Правильность пароля")
            self.log_message("   3. Что файл не открыт в Excel")
        
        self.log_message("=" * 60)
        
        return success

def create_scheduler_bat():
    """Создает BAT файл для Планировщика заданий"""
    
    bat_content = '''@echo off
chcp 1251 > nul
title Автоматическое копирование файла
echo ========================================
echo    АВТОМАТИЧЕСКОЕ КОПИРОВАНИЕ ФАЙЛА
echo ========================================
echo.
echo Дата: %date% Время: %time%
echo.

rem Переходим в папку со скриптом
cd /d "D:\\VSC\\project2"

rem Запускаем Python скрипт
python "copy_final.py"

rem Проверяем результат
if %errorlevel% equ 0 (
    echo.
    echo УСПЕШНО: Файл скопирован
    echo %date% %time% - Успех >> "copy_history.log"
) else (
    echo.
    echo ОШИБКА: Не удалось скопировать файл
    echo %date% %time% - Ошибка >> "copy_history.log"
)

echo.
timeout /t 5
exit
'''
    
    with open(r"D:\VSC\project2\run_copy.bat", "w", encoding="cp866") as f:
        f.write(bat_content)
    
    print("✓ Создан BAT файл для Планировщика: run_copy.bat")

def main():
    """Главная функция"""
    
    print("=" * 60)
    print("📋 СКРИПТ КОПИРОВАНИЯ ФАЙЛА ИЗ СЕТЕВОЙ ПАПКИ")
    print("=" * 60)
    print("Настройки:")
    print(f"  Пользователь: alkor\yakovenko")
    print(f"  Источник: \\\\fs.alkor.ru\\ЦАП\\ВнешниеИсточники\\СБ\\Остатки")
    print(f"  Файл: Северо-Поволжский.xlsx")
    print(f"  Назначение: D:\\Ноут\\Летуаль\\Остатки")
    print("=" * 60)
    
    # Создаем объект копировщика
    copier = FileCopier()
    
    # Запускаем копирование
    success = copier.copy_file()
    
    # Предлагаем создать BAT файл для планировщика
    if success and len(sys.argv) > 1 and sys.argv[1] == "--setup":
        print("\n" + "=" * 60)
        print("⚙️  НАСТРОЙКА ДЛЯ ПЛАНИРОВЩИКА ЗАДАНИЙ")
        print("=" * 60)
        create_scheduler_bat()
        
        print("\n📋 ИНСТРУКЦИЯ ДЛЯ ПЛАНИРОВЩИКА:")
        print("1. Откройте Планировщик заданий (Win+R → taskschd.msc)")
        print("2. Создайте задачу:")
        print("   - Имя: 'Копирование Северо-Поволжский.xlsx'")
        print("   - Триггер: Ежедневно в 08:30")
        print("   - Действие: Запустить программу")
        print("   - Программа: D:\\VSC\\project2\\run_copy.bat")
        print("   - Отметьте 'Выполнять с наивысшими правами'")
        print("3. Сохраните и протестируйте")
    
    return 0 if success else 1

if __name__ == "__main__":
    # Выходной код для планировщика (0 = успех, 1 = ошибка)
    exit_code = main()
    sys.exit(exit_code)