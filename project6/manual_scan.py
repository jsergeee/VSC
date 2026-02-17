import subprocess
import socket
from datetime import datetime
import platform
import re
import time
import pandas as pd
import os

# ==================== КОНФИГУРАЦИЯ ====================
INPUT_FILE = r'D:\Ноут\Летуаль\IP адреса СВН.xlsx'

# ==================== УПРОЩЕННЫЕ ФУНКЦИИ ====================
def simple_ping(ip_address):
    """Упрощенный ping с проверкой источника"""
    param = '-n'
    count = '2'
    timeout = '1000'
    
    try:
        command = ['ping', param, count, '-w', timeout, ip_address]
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='cp866',
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        output = result.stdout
        
        if result.returncode == 0:
            # Проверяем, что ответ пришел от нужного IP
            response_pattern = r'Ответ от (\d+\.\d+\.\d+\.\d+)'
            matches = re.findall(response_pattern, output)
            
            if matches:
                # Проверяем все ли ответы от целевого IP
                all_correct = all(ip == ip_address for ip in matches)
                if all_correct:
                    return True, "✅ Доступен"
                else:
                    wrong_ips = set(matches)
                    return False, f"❌ Ответ от другого IP: {', '.join(wrong_ips)}"
            return True, "✅ Доступен"
        else:
            return False, "❌ Нет ответа"
            
    except Exception:
        return False, "❌ Ошибка выполнения"

def check_port(ip_address, port=80, timeout=2):
    """Проверка порта"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip_address, port))
        sock.close()
        
        return result == 0
    except:
        return False

def read_ip_list_from_excel(file_path):
    """Чтение списка IP-адресов из Excel файла"""
    try:
        # Проверяем существование файла
        if not os.path.exists(file_path):
            print(f"❌ Файл не найден: {file_path}")
            return []
        
        # Читаем Excel файл
        df = pd.read_excel(file_path)
        
        # Проверяем необходимые колонки
        # Ищем колонки с именами хостов и IP-адресами
        host_column = None
        ip_column = None
        
        # Пробуем найти колонки по типичным названиям
        possible_host_names = ['Имя', 'Название', 'Hostname', 'Имя хоста', 'Название устройства']
        possible_ip_names = ['IP', 'IP адрес', 'Адрес', 'IP-адрес']
        
        for col in df.columns:
            col_lower = str(col).lower()
            if any(name.lower() in col_lower for name in possible_host_names):
                host_column = col
            if any(name.lower() in col_lower for name in possible_ip_names):
                ip_column = col
        
        # Если не нашли по именам, используем первые две колонки
        if host_column is None or ip_column is None:
            if len(df.columns) >= 2:
                host_column = df.columns[0]
                ip_column = df.columns[1]
                print(f"⚠️  Использую колонки: {host_column} (имена) и {ip_column} (IP)")
            else:
                print("❌ В файле недостаточно колонок")
                return []
        
        # Формируем список
        ip_list = []
        for index, row in df.iterrows():
            host = str(row[host_column]).strip()
            ip = str(row[ip_column]).strip()
            
            # Проверяем валидность IP-адреса
            if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
                ip_list.append((host, ip))
            else:
                print(f"⚠️  Пропущен некорректный IP: {ip} для хоста {host}")
        
        print(f"📊 Прочитано {len(ip_list)} валидных адресов из файла")
        return ip_list
        
    except Exception as e:
        print(f"❌ Ошибка чтения Excel файла: {e}")
        return []

# ==================== ОСНОВНАЯ ФУНКЦИЯ ====================
def main():
    """Упрощенное сканирование с выводом в терминал"""
    
    # Читаем IP-адреса из файла
    print("=" * 70)
    print("📁 ЧТЕНИЕ ФАЙЛА С IP АДРЕСАМИ")
    print("=" * 70)
    print(f"Файл: {INPUT_FILE}")
    
    IP_LIST = read_ip_list_from_excel(INPUT_FILE)
    
    if not IP_LIST:
        print("❌ Не удалось загрузить IP-адреса. Проверьте файл.")
        input("\nНажмите Enter для выхода...")
        return
    
    print("\n" + "=" * 70)
    print("🔄 УПРОЩЕННОЕ СКАНИРОВАНИЕ IP АДРЕСОВ")
    print("=" * 70)
    print(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"Всего адресов: {len(IP_LIST)}")
    print("-" * 70)
    
    results = []
    
    for name, ip in IP_LIST:
        print(f"🔍 {name:20} {ip:15}... ", end="", flush=True)
        
        # Пинг
        ping_ok, ping_msg = simple_ping(ip)
        
        # Проверка порта (если ping успешен)
        if ping_ok:
            port_ok = check_port(ip)
            if port_ok:
                result = "✅ Доступен (Ping + порт 80)"
                print(f"✅ Доступен")
            else:
                result = "⚠️  Ping OK, порт 80 закрыт"
                print(f"⚠️  Ping OK, порт закрыт")
        else:
            result = ping_msg
            print(ping_msg.replace("❌ ", ""))
        
        results.append((name, ip, result))
        
        # Небольшая пауза
        time.sleep(0.5)
    
    # Итоговая статистика
    print("\n" + "=" * 70)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("-" * 70)
    
    available = sum(1 for _, _, status in results if "✅" in status)
    problems = sum(1 for _, _, status in results if "⚠️" in status)
    unavailable = sum(1 for _, _, status in results if "❌" in status)
    
    print(f"Всего адресов: {len(IP_LIST)}")
    print(f"✅ Полностью доступны: {available}")
    print(f"⚠️  Только Ping: {problems}")
    print(f"❌ Недоступны: {unavailable}")
    
    # Детали проблемных хостов
    if problems > 0 or unavailable > 0:
        print("\n🚫 ПРОБЛЕМНЫЕ ХОСТЫ:")
        print("-" * 70)
        for name, ip, status in results:
            if "❌" in status or "⚠️" in status:
                print(f"{status}")
                print(f"  {name} - {ip}")
                print()
    
    # Сохранение результатов в файл
    try:
        output_file = f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df_results = pd.DataFrame(results, columns=['Имя', 'IP', 'Статус'])
        df_results.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n💾 Результаты сохранены в файл: {output_file}")
    except Exception as e:
        print(f"\n⚠️  Не удалось сохранить результаты: {e}")
    
    print("=" * 70)
    print(f"Сканирование завершено: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 70)

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Сканирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    
    input("\nНажмите Enter для выхода...")