#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Вспомогательные функции для анализа событий безопасности
"""

import re
import win32evtlog
import pywintypes
import time
import os
import subprocess
import webbrowser
from collections import Counter, defaultdict

# Цвета для консоли
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[35m'
    END = '\033[0m'
    BOLD = '\033[1m'

def escape_html(text):
    """Экранирует HTML специальные символы"""
    if text is None:
        return ""
    text = str(text)
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

def get_events(days=7, log_type='Security'):
    """Получить события безопасности за указанный период"""
    print(f"{Colors.CYAN}📊 Чтение журнала {log_type}...{Colors.END}")
    
    try:
        hand = win32evtlog.OpenEventLog('localhost', log_type)
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        
        total = win32evtlog.GetNumberOfEventLogRecords(hand)
        print(f"  Всего записей в журнале: {total}")
        
        events = []
        events_read = 0
        
        # Время начала периода
        start_time = time.time() - (days * 24 * 60 * 60)
        start_time_struct = time.localtime(start_time)
        py_start_time = pywintypes.Time(time.mktime(start_time_struct))
        
        print(f"  Период: последние {days} дней")
        print(f"  Начало периода: {time.strftime('%Y-%m-%d %H:%M:%S', start_time_struct)}")
        
        while True:
            events_part = win32evtlog.ReadEventLog(hand, flags, 0)
            if not events_part:
                break
            
            for event in events_part:
                if event.TimeGenerated < py_start_time:
                    continue
                    
                events.append(event)
                events_read += 1
                
                if events_read % 1000 == 0:
                    print(f"    Прочитано {events_read} событий...", end='\r')
        
        print(f"\n  {Colors.GREEN}✅ Найдено событий за период: {len(events)}{Colors.END}")
        win32evtlog.CloseEventLog(hand)
        return events
        
    except Exception as e:
        print(f"{Colors.RED}❌ Ошибка чтения журнала: {e}{Colors.END}")
        return []

def extract_subjects_from_event(event):
    """Извлечь информацию о субъектах из события"""
    subjects = {
        "SubjectUserSid": None,
        "SubjectUserName": None,
        "SubjectDomainName": None,
        "SubjectLogonId": None,
        "TargetUserSid": None,
        "TargetUserName": None,
        "TargetDomainName": None,
        "TargetLogonId": None,
        "ProcessId": None,
        "ProcessName": None,
        "IpAddress": None,
        "IpPort": None,
        "Guid": None,
        "LogonType": None,
        "PrivilegeList": None,
        "ServiceName": None,
        "TaskName": None
    }
    
    try:
        event_str = str(event)
        
        # Регулярные выражения для поиска различных полей
        patterns = {
            "SubjectUserSid": r"SubjectUserSid[:\s]*([^\s]+)",
            "SubjectUserName": r"SubjectUserName[:\s]*([^\s]+)",
            "SubjectDomainName": r"SubjectDomainName[:\s]*([^\s]+)",
            "SubjectLogonId": r"SubjectLogonId[:\s]*([^\s]+)",
            "TargetUserSid": r"TargetUserSid[:\s]*([^\s]+)",
            "TargetUserName": r"TargetUserName[:\s]*([^\s]+)",
            "TargetDomainName": r"TargetDomainName[:\s]*([^\s]+)",
            "TargetLogonId": r"TargetLogonId[:\s]*([^\s]+)",
            "ProcessId": r"ProcessId[:\s]*([^\s]+)",
            "ProcessName": r"ProcessName[:\s]*([^\s]+)",
            "IpAddress": r"IpAddress[:\s]*([^\s]+)",
            "IpPort": r"IpPort[:\s]*([^\s]+)",
            "Guid": r"Guid[:\s]*({[^}]+})",
            "LogonType": r"LogonType[:\s]*([^\s]+)",
            "PrivilegeList": r"Privileges[:\s]*(.+?)(?=\n|$)",
            "ServiceName": r"Service Name[:\s]*(.+?)(?=\n|$)",
            "TaskName": r"Task Name[:\s]*(.+?)(?=\n|$)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, event_str, re.IGNORECASE)
            if match:
                subjects[key] = match.group(1).strip()
        
        # Дополнительный анализ для события 4624 (успешный вход)
        if event.EventID == 4624:
            # Для успешного входа TargetUserName содержит имя пользователя
            if not subjects["TargetUserName"] or subjects["TargetUserName"] in ["-", ""]:
                # Пробуем найти альтернативные форматы
                alt_patterns = [
                    r"Account Name[:\s]*([^\s]+)",
                    r"User[:\s]*([^\s]+)",
                    r"UserName[:\s]*([^\s]+)"
                ]
                for pattern in alt_patterns:
                    match = re.search(pattern, event_str, re.IGNORECASE)
                    if match:
                        subjects["TargetUserName"] = match.group(1).strip()
                        break
        
        # Дополнительный анализ для события 4672 (специальные привилегии)
        if event.EventID == 4672:
            if subjects["PrivilegeList"]:
                subjects["Privileges_detail"] = analyze_privileges(subjects["PrivilegeList"])
        
        # Дополнительный анализ IP адреса
        if subjects["IpAddress"] and subjects["IpAddress"] not in ["-", "::", "0.0.0.0", "127.0.0.1", "localhost"]:
            subjects["IpAnalysis"] = analyze_ip_address(subjects["IpAddress"])
        
        # Анализ SID
        if subjects["SubjectUserSid"] and subjects["SubjectUserSid"] not in ["-", "S-1-0-0"]:
            subjects["SidAnalysis"] = analyze_sid(subjects["SubjectUserSid"])
        
        # Анализ типа входа
        if subjects["LogonType"]:
            subjects["LogonTypeDesc"] = get_logon_type_description(subjects["LogonType"])
        
        # Очистка и нормализация имен пользователей
        for field in ["SubjectUserName", "TargetUserName"]:
            if subjects[field] and subjects[field] in ["-", "", "NULL", "None"]:
                subjects[field] = None
        
    except Exception as e:
        print(f"  Ошибка извлечения субъектов: {e}")
    
    return subjects
def analyze_ip_address(ip):
    """Анализ IP адреса"""
    analysis = {
        "type": "Unknown",
        "is_private": False,
        "is_loopback": False,
        "is_multicast": False,
        "geolocation": None
    }
    
    try:
        # Проверка типа IP
        if ":" in ip:
            analysis["type"] = "IPv6"
            # Проверка локальных IPv6 адресов
            if ip.startswith("::1"):
                analysis["is_loopback"] = True
            elif ip.startswith("fe80:"):
                analysis["type"] = "IPv6 Link-Local"
        else:
            analysis["type"] = "IPv4"
            # Проверка специальных IPv4 адресов
            parts = ip.split('.')
            if len(parts) == 4:
                first = int(parts[0])
                second = int(parts[1])
                
                if first == 127:
                    analysis["is_loopback"] = True
                elif first == 10:
                    analysis["is_private"] = True
                elif first == 172 and 16 <= second <= 31:
                    analysis["is_private"] = True
                elif first == 192 and second == 168:
                    analysis["is_private"] = True
                elif first == 169 and second == 254:
                    analysis["type"] = "APIPA"
                elif first >= 224 and first <= 239:
                    analysis["is_multicast"] = True
        
        # Попытка получить геолокацию (только для публичных IP)
        if not analysis["is_private"] and not analysis["is_loopback"] and ip not in ["-", "::"]:
            analysis["geolocation"] = "Внешний IP (требуется дополнительный анализ)"
            
    except Exception as e:
        print(f"  Ошибка анализа IP: {e}")
    
    return analysis

def analyze_sid(sid_string):
    """Анализ SID"""
    analysis = {
        "type": "Unknown",
        "well_known": False,
        "description": None
    }
    
    try:
        # Известные SID
        well_known_sids = {
            "S-1-0-0": "Null Authority",
            "S-1-1-0": "World Authority",
            "S-1-2-0": "Local Authority",
            "S-1-3-0": "Creator Authority",
            "S-1-3-1": "Creator Owner",
            "S-1-3-2": "Creator Group",
            "S-1-3-3": "Creator Owner Server",
            "S-1-3-4": "Creator Group Server",
            "S-1-5-7": "Anonymous",
            "S-1-5-8": "Proxy",
            "S-1-5-9": "Enterprise Domain Controllers",
            "S-1-5-10": "Principal Self",
            "S-1-5-11": "Authenticated Users",
            "S-1-5-12": "Restricted Code",
            "S-1-5-13": "Terminal Server Users",
            "S-1-5-14": "Remote Interactive Logon",
            "S-1-5-15": "This Organization",
            "S-1-5-17": "IUSR",
            "S-1-5-18": "Local System",
            "S-1-5-19": "Local Service",
            "S-1-5-20": "Network Service",
            "S-1-5-32-544": "Administrators",
            "S-1-5-32-545": "Users",
            "S-1-5-32-546": "Guests",
            "S-1-5-32-547": "Power Users",
            "S-1-5-32-548": "Account Operators",
            "S-1-5-32-549": "Server Operators",
            "S-1-5-32-550": "Print Operators",
            "S-1-5-32-551": "Backup Operators",
            "S-1-5-32-552": "Replicators"
        }
        
        if sid_string in well_known_sids:
            analysis["well_known"] = True
            analysis["type"] = "Well-Known"
            analysis["description"] = well_known_sids[sid_string]
        elif sid_string.startswith("S-1-5-21"):
            analysis["type"] = "Domain/Local User"
        elif sid_string.startswith("S-1-5-80"):
            analysis["type"] = "Service"
        elif sid_string == "-":
            analysis["type"] = "Not Available"
            
    except Exception as e:
        print(f"  Ошибка анализа SID: {e}")
    
    return analysis

def get_logon_type_description(logon_type):
    """Получить описание типа входа"""
    logon_types = {
        "2": "Интерактивный (локальный вход)",
        "3": "Сетевой (например, доступ к общим папкам)",
        "4": "Пакетный (запланированные задачи)",
        "5": "Сервис (запуск службы)",
        "7": "Разблокировка рабочей станции",
        "8": "Сетевой с явными учетными данными",
        "9": "Новый учетные данные (RunAs)",
        "10": "Удаленный интерактивный (RDP)",
        "11": "Интерактивный с кэшированными учетными данными"
    }
    return logon_types.get(logon_type, f"Неизвестный тип ({logon_type})")

def analyze_privileges(privilege_list):
    """Анализ привилегий"""
    if not privilege_list:
        return []
    
    privileges = []
    privilege_desc = {
        "SeTcbPrivilege": "Работа как часть операционной системы",
        "SeBackupPrivilege": "Резервное копирование файлов и каталогов",
        "SeRestorePrivilege": "Восстановление файлов и каталогов",
        "SeShutdownPrivilege": "Завершение работы системы",
        "SeTakeOwnershipPrivilege": "Владение файлами и объектами",
        "SeDebugPrivilege": "Отладка программ",
        "SeSystemEnvironmentPrivilege": "Изменение параметров среды",
        "SeSystemtimePrivilege": "Изменение системного времени",
        "SeProfileSingleProcessPrivilege": "Профилирование одного процесса",
        "SeIncreaseBasePriorityPrivilege": "Увеличение приоритета",
        "SeLoadDriverPrivilege": "Загрузка и выгрузка драйверов",
        "SeCreatePagefilePrivilege": "Создание файла подкачки",
        "SeIncreaseQuotaPrivilege": "Увеличение квот",
        "SeChangeNotifyPrivilege": "Обход перекрестной проверки",
        "SeUndockPrivilege": "Отсоединение компьютера",
        "SeManageVolumePrivilege": "Выполнение обслуживания тома",
        "SeImpersonatePrivilege": "Олицетворение клиента",
        "SeCreateGlobalPrivilege": "Создание глобальных объектов",
        "SeTrustedCredManAccessPrivilege": "Доступ к диспетчеру учетных данных"
    }
    
    for priv in privilege_list.split():
        priv_clean = priv.strip()
        if priv_clean in privilege_desc:
            privileges.append({
                "name": priv_clean,
                "description": privilege_desc[priv_clean],
                "risk": "Высокий" if priv_clean in ["SeTcbPrivilege", "SeDebugPrivilege", "SeTakeOwnershipPrivilege", "SeLoadDriverPrivilege"] else "Средний"
            })
        else:
            privileges.append({"name": priv_clean, "description": "Неизвестная привилегия", "risk": "Средний"})
    
    return privileges

def open_in_browser(report_file):
    """Открыть отчет в браузере"""
    chrome_paths = [
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe")
    ]
    
    chrome_found = False
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"\n{Colors.CYAN}🌐 Открываю отчет в Google Chrome...{Colors.END}")
            subprocess.run([path, report_file])
            chrome_found = True
            break
    
    if not chrome_found:
        print(f"\n{Colors.YELLOW}⚠️ Google Chrome не найден. Открываю в браузере по умолчанию...{Colors.END}")
        webbrowser.open(report_file)