import pandas as pd
import subprocess
import os
import socket
from datetime import datetime
import platform
import re
import smtplib
import ssl
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import traceback
import time

# ==================== КОНФИГУРАЦИЯ ====================
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yandex_email_config.json")
INPUT_FILE = r'D:\Ноут\Летуаль\IP адреса СВН.xlsx'
OUTPUT_DIR = r'D:\VSC\project6\ResultPing'
LOG_FILE = os.path.join(OUTPUT_DIR, 'scheduler_log.txt')

# ==================== ФУНКЦИИ ЛОГИРОВАНИЯ ====================
def setup_logging():
    """Настройка логирования для планировщика"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    return LOG_FILE

def log(message, log_to_file=True):
    """Запись лога"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] {message}"
    
    # Вывод в консоль
    print(log_message)
    
    # Запись в файл
    if log_to_file:
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
        except:
            pass

# ==================== ФУНКЦИИ PING ====================
def ping_ip(ip_address):
    """Упрощенная функция ping для планировщика"""
    param = '-n'
    count = '2'
    timeout = '2000'  # Увеличиваем таймаут для планировщика
    target_ip = str(ip_address)
    
    try:
        # Для планировщика используем упрощенный подход
        command = ['ping', param, count, '-w', timeout, target_ip]
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='cp866',
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10  # Таймаут на выполнение команды
        )
        
        output = result.stdout
        
        # Простая проверка - если есть "TTL=" или "время=", считаем доступным
        if result.returncode == 0:
            if 'TTL=' in output or 'время=' in output or 'time=' in output:
                # Проверяем, что ответ от нужного IP
                response_pattern = r'Ответ от (\d+\.\d+\.\d+\.\d+)'
                matches = re.findall(response_pattern, output)
                
                if matches:
                    all_from_target = all(match == target_ip for match in matches)
                    if all_from_target:
                        return "Доступен", "OK"
                    else:
                        different_ips = set(matches)
                        return "Не доступен", f"Ответ от другого IP: {', '.join(different_ips)}"
                return "Доступен", "OK"
            else:
                return "Не доступен", "Нет ответа"
        else:
            return "Не доступен", "Нет ответа"
            
    except subprocess.TimeoutExpired:
        return "Таймаут", "Превышено время ожидания"
    except Exception as e:
        return "Ошибка", str(e)

def check_port_80(ip_address):
    """Упрощенная проверка порта 80"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # Увеличиваем таймаут
        result = sock.connect_ex((str(ip_address), 80))
        sock.close()
        
        if result == 0:
            return "Открыт"
        else:
            return "Закрыт"
    except socket.timeout:
        return "Таймаут"
    except Exception:
        return "Ошибка"

# ==================== ФУНКЦИИ EMAIL (СПЕЦИАЛЬНО ДЛЯ ПЛАНИРОВЩИКА) ====================
def send_email_for_scheduler(subject, body):
    """Специальная функция отправки email для планировщика"""
    
    # Пробуем несколько раз с задержкой
    for attempt in range(3):
        try:
            log(f"Попытка отправки email #{attempt + 1}")
            
            # Загружаем конфигурацию с абсолютным путем
            config_path = CONFIG_FILE
            if not os.path.exists(config_path):
                log(f"Файл конфигурации не найден: {config_path}")
                return False
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Создаем сообщение
            msg = MIMEMultipart()
            msg['From'] = config['sender_email']
            msg['To'] = config['receiver_email']
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Настройки для планировщика
            smtp_server = config['smtp_server']
            smtp_port = config['smtp_port']
            
            log(f"Подключение к {smtp_server}:{smtp_port}")
            
            # Устанавливаем увеличенные таймауты
            socket.setdefaulttimeout(60)
            
            if smtp_port == 465:
                # SSL соединение
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    smtp_server, 
                    smtp_port, 
                    context=context, 
                    timeout=60
                )
            else:
                # STARTTLS
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=60)
                server.starttls()
            
            # Аутентификация с увеличенным таймаутом
            log("Аутентификация...")
            server.login(config['sender_email'], config['password'])
            log("Аутентификация успешна")
            
            # Отправка
            log("Отправка письма...")
            server.send_message(msg)
            
            # Корректное закрытие
            server.quit()
            
            log("✅ Email успешно отправлен!")
            return True
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            log(f"❌ Ошибка отправки (попытка {attempt + 1}): {error_type}: {error_msg}")
            
            # Если это не последняя попытка, ждем и пробуем снова
            if attempt < 2:
                wait_time = (attempt + 1) * 10  # 10, 20, 30 секунд
                log(f"Жду {wait_time} секунд перед следующей попыткой...")
                time.sleep(wait_time)
            else:
                # На последней попытке сохраняем детали ошибки
                log("Детали ошибки:")
                log(traceback.format_exc())
    
    return False

# ==================== ОСНОВНАЯ ЛОГИКА ====================
def main():
    """Основная функция, оптимизированная для планировщика"""
    
    # Инициализируем логирование
    log_file = setup_logging()
    log("="*70)
    log("ЗАПУСК СКРИПТА МОНИТОРИНГА ИЗ ПЛАНИРОВЩИКА")
    log("="*70)
    log(f"Рабочая директория: {os.getcwd()}")
    log(f"Директория скрипта: {os.path.dirname(os.path.abspath(__file__))}")
    
    try:
        # 1. Проверяем доступность файлов
        log(f"Проверка файла конфигурации: {CONFIG_FILE}")
        if not os.path.exists(CONFIG_FILE):
            log(f"❌ Файл конфигурации не найден!")
            return False
        
        log(f"Проверка входного файла: {INPUT_FILE}")
        if not os.path.exists(INPUT_FILE):
            log(f"❌ Входной файл не найден!")
            return False
        
        # 2. Читаем Excel файл
        log("Чтение Excel файла...")
        try:
            df = pd.read_excel(INPUT_FILE)
            log(f"Успешно прочитано {len(df)} записей")
        except Exception as e:
            log(f"❌ Ошибка чтения Excel: {e}")
            send_email_for_scheduler(
                "ОШИБКА МОНИТОРИНГА - Не удалось прочитать файл",
                f"Ошибка при чтении файла {INPUT_FILE}:\n\n{str(e)}\n\n{traceback.format_exc()}"
            )
            return False
        
        # 3. Проверяем и подготавливаем данные
        required_columns = ['Магазин', 'IP']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            if len(df.columns) >= 2:
                df.columns = ['Магазин', 'IP'] + list(df.columns[2:])
                log("Использованы первые два столбца как 'Магазин' и 'IP'")
            else:
                log(f"❌ Не хватает столбцов: {missing_columns}")
                return False
        
        # 4. Добавляем столбцы для результатов
        df['Статус Ping'] = ''
        df['Детали Ping'] = ''
        df['Статус порта 80'] = ''
        df['Время проверки'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 5. Выполняем проверку хостов
        log(f"Начинаю проверку {len(df)} хостов...")
        
        results = []
        for index, row in df.iterrows():
            store = row['Магазин']
            ip = row['IP']
            
            log(f"Проверка: {store} - {ip}")
            
            # Ping
            ping_status, ping_details = ping_ip(ip)
            df.at[index, 'Статус Ping'] = ping_status
            df.at[index, 'Детали Ping'] = ping_details
            
            # Проверка порта 80
            if ping_status == "Доступен":
                port_status = check_port_80(ip)
            else:
                port_status = "Не проверялся"
            
            df.at[index, 'Статус порта 80'] = port_status
            
            # Сохраняем результат
            results.append({
                'Магазин': store,
                'IP': ip,
                'Ping': ping_status,
                'Детали Ping': ping_details,
                'Порт 80': port_status,
                'Статус': '✅ OK' if ping_status == "Доступен" and port_status == "Открыт" else '⚠️ Проблема'
            })
            
            # Небольшая пауза между проверками
            time.sleep(0.1)
        
        log("Проверка завершена")
        
        # 6. Анализируем результаты
        total = len(df)
        available = len(df[df['Статус Ping'] == 'Доступен'])
        port_open = len(df[df['Статус порта 80'] == 'Открыт'])
        fully_available = len(df[(df['Статус Ping'] == 'Доступен') & 
                               (df['Статус порта 80'] == 'Открыт')])
        
        # 7. Сохраняем результаты в Excel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(OUTPUT_DIR, f'results_{timestamp}.xlsx')
        
        try:
            df.to_excel(output_file, index=False, engine='openpyxl')
            log(f"Результаты сохранены: {output_file}")
        except Exception as e:
            log(f"❌ Ошибка сохранения Excel: {e}")
            # Продолжаем работу, даже если не удалось сохранить Excel
        
        # 8. Создаем текстовый отчет
        report_file = os.path.join(OUTPUT_DIR, f'report_{timestamp}.txt')
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("="*70 + "\n")
                f.write("ОТЧЕТ ПРОВЕРКИ ДОСТУПНОСТИ ХОСТОВ\n")
                f.write("="*70 + "\n")
                f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Всего хостов: {total}\n")
                f.write(f"Доступны по Ping: {available}\n")
                f.write(f"Порт 80 открыт: {port_open}\n")
                f.write(f"Полностью доступны: {fully_available}\n")
                f.write(f"Проблемных хостов: {total - fully_available}\n\n")
                
                # Проблемные хосты
                problem_hosts = df[(df['Статус Ping'] != 'Доступен') | 
                                  (df['Статус порта 80'] != 'Открыт')]
                
                if len(problem_hosts) > 0:
                    f.write("ПРОБЛЕМНЫЕ ХОСТЫ:\n")
                    f.write("="*70 + "\n")
                    for _, row in problem_hosts.iterrows():
                        f.write(f"{row['Магазин']} - {row['IP']}\n")
                        f.write(f"  Ping: {row['Статус Ping']}")
                        if row['Детали Ping'] and row['Детали Ping'] != "OK":
                            f.write(f" ({row['Детали Ping']})")
                        f.write(f"\n  Порт 80: {row['Статус порта 80']}\n\n")
            
            log(f"Текстовый отчет сохранен: {report_file}")
        except Exception as e:
            log(f"❌ Ошибка создания текстового отчета: {e}")
        
        # 9. Формируем и отправляем email
        email_subject = f"Отчет мониторинга - {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        email_body = f"""Отчет проверки доступности хостов
Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

СТАТИСТИКА:
===========
Всего хостов: {total}
Доступны по Ping: {available}
Порт 80 открыт: {port_open}
Полностью доступны: {fully_available}
Проблемных хостов: {total - fully_available}

"""
        
        problem_hosts = df[(df['Статус Ping'] != 'Доступен') | 
                          (df['Статус порта 80'] != 'Открыт')]
        
        if len(problem_hosts) > 0:
            email_body += "ПРОБЛЕМНЫЕ ХОСТЫ:\n"
            email_body += "="*50 + "\n"
            for i, (_, row) in enumerate(problem_hosts.iterrows(), 1):
                email_body += f"{i}. {row['Магазин']} ({row['IP']})\n"
                email_body += f"   Ping: {row['Статус Ping']}"
                if row['Детали Ping'] and row['Детали Ping'] != "OK":
                    email_body += f" ({row['Детали Ping']})"
                email_body += f"\n   Порт 80: {row['Статус порта 80']}\n\n"
        
        email_body += f"\nФайлы с отчетами:\n{output_file}\n{report_file}\n{LOG_FILE}"
        
        # 10. Отправляем email
        log("="*70)
        log("ОТПРАВКА EMAIL ОТЧЕТА")
        log("="*70)
        
        email_sent = send_email_for_scheduler(email_subject, email_body)
        
        if email_sent:
            log("✅ ОТЧЕТ УСПЕШНО ОТПРАВЛЕН ПО EMAIL!")
        else:
            log("❌ НЕ УДАЛОСЬ ОТПРАВИТЬ EMAIL ОТЧЕТ")
            
            # Сохраняем email в файл как запасной вариант
            backup_email_file = os.path.join(OUTPUT_DIR, f'email_backup_{timestamp}.txt')
            try:
                with open(backup_email_file, 'w', encoding='utf-8') as f:
                    f.write(f"Subject: {email_subject}\n\n")
                    f.write(email_body)
                log(f"✅ Email сохранен в файл: {backup_email_file}")
            except:
                log("❌ Не удалось сохранить backup email")
        
        # 11. Финальный отчет
        log("="*70)
        log("МОНИТОРИНГ ЗАВЕРШЕН")
        log(f"Всего хостов: {total}")
        log(f"Полностью доступны: {fully_available}")
        log(f"Проблемных: {total - fully_available}")
        log("="*70)
        
        return True
        
    except Exception as e:
        log(f"❌ КРИТИЧЕСКАЯ ОШИБКА В ОСНОВНОМ ПРОЦЕССЕ: {e}")
        log(traceback.format_exc())
        
        # Пытаемся отправить email об ошибке
        try:
            send_email_for_scheduler(
                "КРИТИЧЕСКАЯ ОШИБКА МОНИТОРИНГА",
                f"Произошла критическая ошибка при выполнении мониторинга:\n\n{str(e)}\n\n{traceback.format_exc()}"
            )
        except:
            pass
        
        return False

if __name__ == "__main__":
    # Устанавливаем кодировку для Windows
    if platform.system() == 'Windows':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
    
    # Запускаем основной процесс
    success = main()
    
    # Гарантированное завершение
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Явный выход с кодом
    exit_code = 0 if success else 1
    log(f"Завершение с кодом: {exit_code}")
    sys.exit(exit_code)