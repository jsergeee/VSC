#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ПОЛНЫЙ АНАЛИЗ СОБЫТИЙ БЕЗОПАСНОСТИ WINDOWS С ПРИВЯЗКОЙ К CVE
Версия: 3.14 (совместимая с Python 3.13)
Основан на официальной документации Microsoft и базе CVE
"""

import win32evtlog
import win32evtlogutil
import win32security
import win32con
import win32api
import win32file
import win32net
import win32netcon
import pywintypes
import datetime
import time
import os
import sys
import re
from collections import Counter, defaultdict
import webbrowser
import tempfile
import subprocess
import ctypes
import json
import urllib.request
import socket
import struct

# Проверка прав администратора
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    print("❌ ОШИБКА: Недостаточно прав!")
    print("Журнал 'Security' требует запуска от имени Администратора.")
    print("\n📋 Решение:")
    print("1. Закройте это окно")
    print("2. Нажмите правой кнопкой на скрипт")
    print("3. Выберите 'Запуск от имени администратора'")
    input("\nНажмите Enter для выхода...")
    sys.exit(1)

# Функция экранирования HTML (для Python 3.13)
def escape_html(text):
    """Экранирует HTML специальные символы (совместимо с Python 3.13)"""
    if text is None:
        return ""
    text = str(text)
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

# Константы для журнала событий
SERVER = 'localhost'
LOG_TYPE = 'Security'
FLAGS = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

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

# База данных CVE для событий безопасности
CVE_DATABASE = {
    # Критические уязвимости, связанные с событиями безопасности
    4624: {
        "cves": [
            {
                "id": "CVE-2021-42287",
                "description": "Active Directory Elevation of Privilege Vulnerability",
                "severity": "Critical",
                "affected": "Windows Server 2008-2022",
                "remediation": "Установите обновление KB5008602 или более позднее"
            },
            {
                "id": "CVE-2021-42291",
                "description": "Active Directory Elevation of Privilege Vulnerability",
                "severity": "High",
                "affected": "Windows Server 2008-2022",
                "remediation": "Установите обновление KB5008602 или более позднее"
            }
        ]
    },
    4625: {
        "cves": [
            {
                "id": "CVE-2022-26931",
                "description": "Windows Kerberos Elevation of Privilege Vulnerability",
                "severity": "High",
                "affected": "Windows 10/11, Server 2019-2022",
                "remediation": "Установите обновление KB5013942 или более позднее"
            }
        ]
    },
    4672: {
        "cves": [
            {
                "id": "CVE-2022-21874",
                "description": "Windows Security Center API Elevation of Privilege Vulnerability",
                "severity": "High",
                "affected": "Windows 10/11, Server 2019-2022",
                "remediation": "Установите обновление KB5009543 или более позднее"
            }
        ]
    },
    4688: {
        "cves": [
            {
                "id": "CVE-2022-30190",
                "description": "Microsoft Office MSHTML Remote Code Execution Vulnerability (Follina)",
                "severity": "Critical",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5015010 или более позднее"
            }
        ]
    },
    4697: {
        "cves": [
            {
                "id": "CVE-2022-34715",
                "description": "Windows Network File System Remote Code Execution Vulnerability",
                "severity": "Critical",
                "affected": "Windows Server 2012-2022",
                "remediation": "Установите обновление KB5016622 или более позднее"
            }
        ]
    },
    4698: {
        "cves": [
            {
                "id": "CVE-2022-26925",
                "description": "Windows LSA Spoofing Vulnerability",
                "severity": "High",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5013942 или более позднее"
            }
        ]
    },
    4720: {
        "cves": [
            {
                "id": "CVE-2022-26919",
                "description": "Active Directory Privilege Escalation Vulnerability",
                "severity": "Critical",
                "affected": "Windows Server 2008-2022",
                "remediation": "Установите обновление KB5013942 или более позднее"
            }
        ]
    },
    4740: {
        "cves": [
            {
                "id": "CVE-2021-33781",
                "description": "Active Directory Security Feature Bypass Vulnerability",
                "severity": "High",
                "affected": "Windows Server 2008-2022",
                "remediation": "Установите обновление KB5004945 или более позднее"
            }
        ]
    },
    4768: {
        "cves": [
            {
                "id": "CVE-2021-33782",
                "description": "Windows Kerberos Elevation of Privilege Vulnerability",
                "severity": "Critical",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5004945 или более позднее"
            },
            {
                "id": "CVE-2022-33679",
                "description": "Windows Kerberos Elevation of Privilege Vulnerability",
                "severity": "Critical",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5016622 или более позднее"
            }
        ]
    },
    4769: {
        "cves": [
            {
                "id": "CVE-2022-33647",
                "description": "Windows Kerberos Elevation of Privilege Vulnerability",
                "severity": "High",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5016622 или более позднее"
            }
        ]
    },
    4771: {
        "cves": [
            {
                "id": "CVE-2021-42287",
                "description": "Active Directory Elevation of Privilege Vulnerability",
                "severity": "Critical",
                "affected": "Windows Server 2008-2022",
                "remediation": "Установите обновление KB5008602 или более позднее"
            }
        ]
    },
    4776: {
        "cves": [
            {
                "id": "CVE-2022-23258",
                "description": "Windows Print Spooler Elevation of Privilege Vulnerability",
                "severity": "High",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5011495 или более позднее"
            }
        ]
    },
    4782: {
        "cves": [
            {
                "id": "CVE-2022-24521",
                "description": "Windows Common Log File System Driver Elevation of Privilege Vulnerability",
                "severity": "Critical",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5011486 или более позднее"
            }
        ]
    },
    4794: {
        "cves": [
            {
                "id": "CVE-2022-26931",
                "description": "Windows Kerberos Elevation of Privilege Vulnerability",
                "severity": "High",
                "affected": "Windows Server 2008-2022",
                "remediation": "Установите обновление KB5013942 или более позднее"
            }
        ]
    },
    5038: {
        "cves": [
            {
                "id": "CVE-2022-21894",
                "description": "Secure Boot Security Feature Bypass Vulnerability",
                "severity": "Critical",
                "affected": "Windows 8-11, Server 2012-2022",
                "remediation": "Обновите прошивку UEFI и установите обновление KB5012170"
            }
        ]
    },
    5140: {
        "cves": [
            {
                "id": "CVE-2022-30136",
                "description": "Windows Network File System Remote Code Execution Vulnerability",
                "severity": "Critical",
                "affected": "Windows Server 2012-2022",
                "remediation": "Установите обновление KB5015010 или более позднее"
            }
        ]
    },
    5827: {
        "cves": [
            {
                "id": "CVE-2020-1472",
                "description": "Netlogon Elevation of Privilege Vulnerability (Zerologon)",
                "severity": "Critical",
                "affected": "Windows Server 2008-2019",
                "remediation": "Установите обновление KB4565349 и включите режим защиты"
            }
        ]
    },
    5828: {
        "cves": [
            {
                "id": "CVE-2020-1472",
                "description": "Netlogon Elevation of Privilege Vulnerability (Zerologon)",
                "severity": "Critical",
                "affected": "Windows Server 2008-2019",
                "remediation": "Установите обновление KB4565349 и включите режим защиты"
            }
        ]
    },
    
    # PowerShell связанные CVE
    4103: {
        "cves": [
            {
                "id": "CVE-2022-41076",
                "description": "PowerShell Remote Code Execution Vulnerability",
                "severity": "Critical",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5018410 или более позднее"
            }
        ]
    },
    4104: {
        "cves": [
            {
                "id": "CVE-2022-41076",
                "description": "PowerShell Remote Code Execution Vulnerability",
                "severity": "Critical",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5018410 или более позднее"
            }
        ]
    },
    
    # Windows Defender
    1116: {
        "cves": [
            {
                "id": "CVE-2022-23278",
                "description": "Microsoft Defender Elevation of Privilege Vulnerability",
                "severity": "High",
                "affected": "Windows Defender на Windows 10/11, Server",
                "remediation": "Обновите определения и установите обновление KB5011486"
            }
        ]
    }
}

# Функция для получения CVE по событию и контексту
def get_cve_for_event(event_id, event_data=None):
    """Получить CVE связанные с событием с учетом контекста"""
    cves = []
    
    if event_id in CVE_DATABASE:
        for cve in CVE_DATABASE[event_id]["cves"]:
            cve_entry = cve.copy()
            
            # Дополнительный анализ на основе данных события
            if event_data:
                # Проверяем специфичные индикаторы для Zerologon
                if cve["id"] == "CVE-2020-1472" and event_id in [5827, 5828]:
                    cve_entry["confidence"] = "High"
                    cve_entry["context_indicators"] = ["Обнаружена попытка использования Zerologon"]
                
                # Проверяем для Follina
                if cve["id"] == "CVE-2022-30190" and event_id == 4688:
                    if "msdt.exe" in str(event_data) or "computerdefault" in str(event_data).lower():
                        cve_entry["confidence"] = "Critical"
                        cve_entry["context_indicators"] = ["Обнаружен запуск msdt.exe - индикатор Follina"]
                
                # Проверяем для PrintNightmare
                if "spoolsv.exe" in str(event_data) and "RpcAddPrinterDriver" in str(event_data):
                    cve_entry["cves"].append({
                        "id": "CVE-2021-34527",
                        "description": "Windows Print Spooler Remote Code Execution Vulnerability (PrintNightmare)",
                        "severity": "Critical"
                    })
            
            cves.append(cve_entry)
    
    return cves

# Функция для извлечения субъектов из события
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
        "Guid": None
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
            "Guid": r"Guid[:\s]*({[^}]+})"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, event_str, re.IGNORECASE)
            if match:
                subjects[key] = match.group(1).strip()
        
        # Дополнительный анализ IP адреса
        if subjects["IpAddress"] and subjects["IpAddress"] not in ["-", "::", "0.0.0.0"]:
            subjects["IpAnalysis"] = analyze_ip_address(subjects["IpAddress"])
        
        # Анализ SID
        if subjects["SubjectUserSid"] and subjects["SubjectUserSid"] not in ["-", "S-1-0-0"]:
            subjects["SidAnalysis"] = analyze_sid(subjects["SubjectUserSid"])
        
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
            # Здесь можно добавить API геолокации, но для примера оставим заглушку
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

def get_event_description(event_id):
    """Получить описание события из базы данных"""
    if event_id in EVENT_DATABASE:
        return EVENT_DATABASE[event_id]
    
    # Определение по диапазону
    if 4600 <= event_id <= 4699:
        return {"desc": f"Событие аудита {event_id}", "category": "Аудит", "level": "Information"}
    elif 4700 <= event_id <= 4799:
        return {"desc": f"Событие политик {event_id}", "category": "Политики", "level": "Information"}
    elif 4800 <= event_id <= 4899:
        return {"desc": f"Событие сессий {event_id}", "category": "Сессии", "level": "Information"}
    elif 4900 <= event_id <= 4999:
        return {"desc": f"Событие безопасности {event_id}", "category": "Безопасность", "level": "Information"}
    else:
        return {"desc": f"Неизвестное событие {event_id}", "category": "Другое", "level": "Unknown"}

def get_level_color(level):
    """Получить цвет для уровня критичности"""
    colors = {
        "Critical": "#e74c3c",
        "Failure": "#e74c3c",
        "Error": "#e74c3c",
        "Warning": "#f39c12",
        "Success": "#27ae60",
        "Information": "#3498db",
        "Unknown": "#7f8c8d"
    }
    return colors.get(level, "#7f8c8d")

def get_events(days=7):
    """Получить события безопасности за указанный период"""
    print(f"{Colors.CYAN}📊 Чтение журнала безопасности...{Colors.END}")
    
    try:
        hand = win32evtlog.OpenEventLog(SERVER, LOG_TYPE)
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

def analyze_events(events):
    """Анализ событий"""
    print(f"{Colors.CYAN}📈 Анализ событий...{Colors.END}")
    
    # Статистика по ID событий
    event_counter = Counter()
    critical_events_with_subjects = []
    
    for event in events:
        event_counter[event.EventID] += 1
        
        # Для критических событий собираем детальную информацию о субъектах
        event_info = get_event_description(event.EventID)
        if event_info['level'] in ['Critical', 'Failure', 'Error']:
            subjects = extract_subjects_from_event(event)
            cves = get_cve_for_event(event.EventID, event)
            
            critical_events_with_subjects.append({
                'event': event,
                'info': event_info,
                'subjects': subjects,
                'cves': cves,
                'timestamp': event.TimeGenerated
            })
    
    # Собираем все уникальные ID (из базы и из журнала)
    all_ids = set(EVENT_DATABASE.keys()) | set(event_counter.keys())
    
    # Детальная статистика
    detailed_stats = []
    for event_id in sorted(all_ids):
        info = get_event_description(event_id)
        count = event_counter.get(event_id, 0)
        
        # Добавляем информацию о CVE
        cves = get_cve_for_event(event_id)
        
        detailed_stats.append({
            'id': event_id,
            'description': info['desc'],
            'category': info['category'],
            'level': info['level'],
            'count': count,
            'cves': cves
        })
    
    # Статистика по категориям
    category_stats = defaultdict(lambda: {'total': 0, 'types': set(), 'critical': 0})
    for stat in detailed_stats:
        if stat['count'] > 0:
            category_stats[stat['category']]['total'] += stat['count']
            category_stats[stat['category']]['types'].add(stat['id'])
            if stat['level'] in ['Critical', 'Failure', 'Error']:
                category_stats[stat['category']]['critical'] += stat['count']
    
    # Общая статистика
    total_events = len(events)
    unique_types = len(event_counter)
    critical_count = len([e for e in events if get_event_description(e.EventID)['level'] in ['Critical', 'Failure', 'Error']])
    
    return {
        'detailed': detailed_stats,
        'category_stats': category_stats,
        'total_events': total_events,
        'unique_types': unique_types,
        'critical_count': critical_count,
        'critical_events_with_subjects': critical_events_with_subjects,
        'event_counter': event_counter
    }

def generate_html_report(analysis, days, output_file):
    """Генерация HTML отчета"""
    print(f"{Colors.CYAN}🛠️  Создание HTML отчета...{Colors.END}")
    
    # Форматирование дат
    start_time = time.time() - (days * 24 * 60 * 60)
    start_time_str = time.strftime('%d.%m.%Y %H:%M', time.localtime(start_time))
    end_time_str = time.strftime('%d.%m.%Y %H:%M', time.localtime())
    generation_time = time.strftime('%d.%m.%Y %H:%M:%S', time.localtime())
    
    # Сортировка для топ-10
    top_events = sorted([e for e in analysis['detailed'] if e['count'] > 0], 
                       key=lambda x: x['count'], reverse=True)[:10]
    
    # Категории для отображения
    categories = []
    for cat, data in analysis['category_stats'].items():
        percentage = (data['total'] / analysis['total_events'] * 100) if analysis['total_events'] > 0 else 0
        critical_percentage = (data['critical'] / data['total'] * 100) if data['total'] > 0 else 0
        categories.append({
            'name': cat,
            'total': data['total'],
            'types': len(data['types']),
            'critical': data['critical'],
            'percentage': percentage,
            'critical_percentage': critical_percentage
        })
    categories.sort(key=lambda x: x['total'], reverse=True)
    
    # Создание HTML
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Полный анализ событий безопасности Windows с CVE</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2c3e50, #4a6491);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            text-align: center;
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-card .number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 10px;
        }}
        
        .stat-card .label {{
            font-size: 0.9em;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-card.critical .number {{
            color: #e74c3c;
        }}
        
        .cve-section {{
            padding: 30px;
            background: #fff3cd;
            border-left: 4px solid #f39c12;
            margin: 20px 30px;
            border-radius: 5px;
        }}
        
        .cve-section h2 {{
            color: #856404;
            margin-bottom: 15px;
        }}
        
        .cve-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        
        .cve-item {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #e74c3c;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        .cve-id {{
            font-size: 1.2em;
            font-weight: bold;
            color: #c0392b;
            margin-bottom: 5px;
        }}
        
        .cve-desc {{
            color: #555;
            margin-bottom: 10px;
        }}
        
        .cve-severity {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            background: #e74c3c;
            color: white;
            margin-right: 5px;
        }}
        
        .cve-remediation {{
            font-size: 0.9em;
            color: #27ae60;
            margin-top: 10px;
        }}
        
        .critical-events {{
            padding: 0 30px 30px 30px;
        }}
        
        .critical-events h2 {{
            color: #c0392b;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e74c3c;
        }}
        
        .critical-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }}
        
        .critical-item {{
            background: #fdf2f2;
            border: 1px solid #f5c6cb;
            border-radius: 8px;
            padding: 20px;
        }}
        
        .critical-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .critical-id {{
            font-size: 1.3em;
            font-weight: bold;
            color: #721c24;
        }}
        
        .critical-time {{
            color: #856404;
            font-size: 0.9em;
        }}
        
        .subjects-table {{
            width: 100%;
            margin-top: 15px;
            border-collapse: collapse;
        }}
        
        .subjects-table td {{
            padding: 8px;
            border-bottom: 1px solid #f5c6cb;
        }}
        
        .subjects-table td:first-child {{
            font-weight: bold;
            width: 40%;
        }}
        
        .top-events {{
            padding: 0 30px 30px 30px;
        }}
        
        .top-events h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }}
        
        .top-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }}
        
        .top-item {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .top-item .event-id {{
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .top-item .event-desc {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }}
        
        .top-item .event-count {{
            font-size: 1.5em;
            font-weight: bold;
        }}
        
        .category-stats {{
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .category-stats h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }}
        
        .category-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }}
        
        .category-item {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        .category-item.critical {{
            border-left-color: #e74c3c;
        }}
        
        .category-item h3 {{
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .category-item p {{
            color: #555;
        }}
        
        .category-item .critical-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            background: #e74c3c;
            color: white;
            font-size: 0.8em;
            margin-left: 10px;
        }}
        
        .events-table {{
            padding: 30px;
            overflow-x: auto;
        }}
        
        .events-table h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }}
        
        th {{
            background: #2c3e50;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            cursor: pointer;
        }}
        
        th:hover {{
            background: #34495e;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        tr:hover {{
            background: #f5f7fa;
        }}
        
        .event-id {{
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .count {{
            text-align: center;
            font-weight: bold;
            border-radius: 20px;
            padding: 5px 10px;
            display: inline-block;
            min-width: 60px;
        }}
        
        .count-0 {{ background: #ecf0f1; color: #7f8c8d; }}
        .count-1 {{ background: #d5f4e6; color: #27ae60; }}
        .count-low {{ background: #fff3cd; color: #856404; }}
        .count-medium {{ background: #f8d7da; color: #721c24; }}
        .count-high {{ background: #721c24; color: white; }}
        
        .level-badge {{
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .cve-badge {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            background: #c0392b;
            color: white;
            font-size: 0.7em;
            margin-right: 3px;
            margin-bottom: 3px;
        }}
        
        .search-box {{
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 12px 20px;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 16px;
            transition: border-color 0.3s;
        }}
        
        .search-box input:focus {{
            outline: none;
            border-color: #3498db;
        }}
        
        .footer {{
            background: #34495e;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.9em;
        }}
        
        .highlight {{
            background: yellow;
            padding: 2px;
            border-radius: 3px;
        }}
        
        .tooltip {{
            position: relative;
            display: inline-block;
            cursor: help;
        }}
        
        .tooltip .tooltiptext {{
            visibility: hidden;
            width: 200px;
            background-color: #555;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -100px;
            opacity: 0;
            transition: opacity 0.3s;
        }}
        
        .tooltip:hover .tooltiptext {{
            visibility: visible;
            opacity: 1;
        }}
        
        @media (max-width: 768px) {{
            .summary {{
                grid-template-columns: 1fr;
            }}
            
            .category-grid {{
                grid-template-columns: 1fr;
            }}
            
            th, td {{
                padding: 10px;
                font-size: 14px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Полный анализ событий безопасности Windows с привязкой к CVE</h1>
            <div class="subtitle">
                <p>Период анализа: {start_time_str} - {end_time_str}</p>
                <p>Отчет сгенерирован: {generation_time}</p>
            </div>
        </div>
        
        <div class="summary">
            <div class="stat-card">
                <div class="number">{analysis['total_events']}</div>
                <div class="label">Всего событий</div>
            </div>
            <div class="stat-card">
                <div class="number">{analysis['unique_types']}</div>
                <div class="label">Уникальных типов событий</div>
            </div>
            <div class="stat-card critical">
                <div class="number">{analysis['critical_count']}</div>
                <div class="label">Критических событий</div>
            </div>
            <div class="stat-card">
                <div class="number">{days}</div>
                <div class="label">Дней анализа</div>
            </div>
            <div class="stat-card">
                <div class="number">{len(categories)}</div>
                <div class="label">Категорий событий</div>
            </div>
        </div>
        
        <div class="cve-section">
            <h2>⚠️ CVE Уязвимости, связанные с событиями</h2>
            <div class="cve-grid">
"""
    
    # Добавляем уникальные CVE из критических событий
    cve_set = set()
    for event in analysis['critical_events_with_subjects']:
        for cve in event['cves']:
            cve_key = cve['id']
            if cve_key not in cve_set:
                cve_set.add(cve_key)
                html += f"""
                <div class="cve-item">
                    <div class="cve-id">{cve['id']}</div>
                    <div class="cve-desc">{escape_html(cve['description'])}</div>
                    <div><span class="cve-severity">{cve['severity']}</span></div>
                    <div class="cve-remediation">🔧 {escape_html(cve['remediation'])}</div>
                </div>
"""
    
    html += f"""
            </div>
        </div>
        
        <div class="critical-events">
            <h2>🔴 Критические события с детальным анализом субъектов</h2>
            <div class="critical-grid">
"""
    
    # Добавляем критические события с анализом субъектов
    for critical in analysis['critical_events_with_subjects'][:10]:  # Показываем топ-10 критических
        event_time = critical['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(critical['timestamp'], 'strftime') else str(critical['timestamp'])
        subjects = critical['subjects']
        
        html += f"""
                <div class="critical-item">
                    <div class="critical-header">
                        <span class="critical-id">Событие {critical['event'].EventID}</span>
                        <span class="critical-time">{event_time}</span>
                    </div>
                    <div><strong>Описание:</strong> {escape_html(critical['info']['desc'])}</div>
                    
                    <table class="subjects-table">
                        <tr><td>SubjectUserName:</td><td>{escape_html(subjects['SubjectUserName'] or 'Не указан')}</td></tr>
                        <tr><td>SubjectDomainName:</td><td>{escape_html(subjects['SubjectDomainName'] or 'Не указан')}</td></tr>
                        <tr><td>SubjectUserSid:</td><td>{escape_html(subjects['SubjectUserSid'] or 'Не указан')}</td></tr>
"""
        
        if subjects.get('SidAnalysis'):
            sid_info = subjects['SidAnalysis']
            html += f"""<tr><td>SID Analysis:</td><td>{sid_info['type']} - {sid_info.get('description', '')}</td></tr>"""
        
        if subjects['IpAddress'] and subjects['IpAddress'] not in ['-', '::']:
            html += f"""<tr><td>IP Address:</td><td>{escape_html(subjects['IpAddress'])}</td></tr>"""
            if subjects.get('IpAnalysis'):
                ip_info = subjects['IpAnalysis']
                html += f"""<tr><td>IP Type:</td><td>{ip_info['type']}</td></tr>"""
        
        if subjects['ProcessName']:
            html += f"""<tr><td>Process:</td><td>{escape_html(subjects['ProcessName'])}</td></tr>"""
        
        if subjects['Guid']:
            html += f"""<tr><td>GUID:</td><td>{escape_html(subjects['Guid'])}</td></tr>"""
        
        # Добавляем CVE для этого события
        if critical['cves']:
            html += f"""<tr><td colspan="2"><strong>Связанные CVE:</strong><br>"""
            for cve in critical['cves']:
                html += f"""<span class="cve-badge">{cve['id']}</span> """
            html += f"""</td></tr>"""
        
        html += f"""
                    </table>
                </div>
"""
    
    html += f"""
            </div>
        </div>
        
        <div class="top-events">
            <h2>🔥 Топ-10 самых частых событий</h2>
            <div class="top-grid">
"""
    
    # Добавляем топ-10 событий
    for event in top_events:
        html += f"""
                <div class="top-item">
                    <div class="event-id">Событие {event['id']}</div>
                    <div class="event-desc">{escape_html(event['description'])}</div>
                    <div class="event-count">{event['count']} раз</div>
                </div>
"""
    
    html += f"""
            </div>
        </div>
        
        <div class="category-stats">
            <h2>📊 Статистика по категориям</h2>
            <div class="category-grid">
"""
    
    # Добавляем категории
    for cat in categories:
        critical_class = " critical" if cat['critical'] > 0 else ""
        html += f"""
                <div class="category-item{critical_class}">
                    <h3>{escape_html(cat['name'])}{' <span class="critical-badge">крит: ' + str(cat['critical']) + '</span>' if cat['critical'] > 0 else ''}</h3>
                    <p>Событий: {cat['total']} ({cat['percentage']:.1f}%)</p>
                    <p>Типов: {cat['types']}</p>
                </div>
"""
    
    html += f"""
            </div>
        </div>
        
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 Поиск по ID события, описанию или категории..." onkeyup="searchEvents()">
        </div>
        
        <div class="events-table">
            <h2>📋 Детальная статистика событий с CVE</h2>
            <table id="eventsTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">ID события</th>
                        <th onclick="sortTable(1)">Описание</th>
                        <th onclick="sortTable(2)">Категория</th>
                        <th onclick="sortTable(3)">Уровень</th>
                        <th onclick="sortTable(4)">CVE</th>
                        <th onclick="sortTable(5)">Количество</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Добавляем все события
    for event in sorted(analysis['detailed'], key=lambda x: x['id']):
        count_class = "count-0"
        if event['count'] > 0:
            count_class = "count-1"
        if event['count'] > 10:
            count_class = "count-low"
        if event['count'] > 50:
            count_class = "count-medium"
        if event['count'] > 100:
            count_class = "count-high"
        
        level_color = get_level_color(event['level'])
        level_style = f"background: {level_color}; color: white;"
        
        # Форматирование CVE
        cve_html = ""
        if event['cves']:
            for cve in event['cves']:
                cve_html += f'<span class="cve-badge tooltip">{cve["id"]}<span class="tooltiptext">{escape_html(cve["description"])}</span></span> '
        else:
            cve_html = "-"
        
        html += f"""
                    <tr class="event-row" data-id="{event['id']}" data-description="{escape_html(event['description'])}" data-category="{escape_html(event['category'])}">
                        <td><span class="event-id">{event['id']}</span></td>
                        <td>{escape_html(event['description'])}</td>
                        <td>{escape_html(event['category'])}</td>
                        <td><span class="level-badge" style="{level_style}">{event['level']}</span></td>
                        <td>{cve_html}</td>
                        <td><span class="count {count_class}">{event['count']}</span></td>
                    </tr>
"""
    
    html += f"""
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>📄 Основано на официальной документации Microsoft и базе CVE</p>
            <p>⚠️ Критические события требуют немедленного внимания и анализа CVE</p>
            <p>🔄 Версия анализатора: 3.14 (с поддержкой CVE и анализа субъектов)</p>
        </div>
    </div>
    
    <script>
        function searchEvents() {{
            const input = document.getElementById('searchInput');
            const filter = input.value.toLowerCase();
            const rows = document.querySelectorAll('.event-row');
            
            rows.forEach(row => {{
                const id = row.getAttribute('data-id');
                const description = row.getAttribute('data-description').toLowerCase();
                const category = row.getAttribute('data-category').toLowerCase();
                
                if (id.includes(filter) || description.includes(filter) || category.includes(filter)) {{
                    row.style.display = '';
                }} else {{
                    row.style.display = 'none';
                }}
            }});
        }}
        
        let sortDirection = [true, true, true, true, true, true];
        
        function sortTable(columnIndex) {{
            const table = document.getElementById('eventsTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            sortDirection[columnIndex] = !sortDirection[columnIndex];
            
            rows.sort((a, b) => {{
                const aValue = a.cells[columnIndex].textContent.trim();
                const bValue = b.cells[columnIndex].textContent.trim();
                const isNumeric = columnIndex === 0 || columnIndex === 5;
                
                if (isNumeric) {{
                    const aNum = parseInt(aValue) || 0;
                    const bNum = parseInt(bValue) || 0;
                    return sortDirection[columnIndex] ? aNum - bNum : bNum - aNum;
                }} else {{
                    return sortDirection[columnIndex] 
                        ? aValue.localeCompare(bValue) 
                        : bValue.localeCompare(aValue);
                }}
            }});
            
            rows.forEach(row => tbody.appendChild(row));
        }}
    </script>
</body>
</html>
"""
    
    # Сохраняем HTML
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"{Colors.GREEN}✅ Отчет сохранен: {output_file}{Colors.END}")
    return output_file

def main():
    """Основная функция"""
    print(f"{Colors.HEADER}{Colors.BOLD}========================================{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}   ПОЛНЫЙ АНАЛИЗ СОБЫТИЙ БЕЗОПАСНОСТИ   {Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}           С ПРИВЯЗКОЙ К CVE            {Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}========================================{Colors.END}")
    print(f"{Colors.CYAN}Дата запуска: {time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    
    # Запрос количества дней
    try:
        days_input = input(f"{Colors.YELLOW}Введите количество дней для анализа (Enter - 7): {Colors.END}")
        days = int(days_input) if days_input.strip() else 7
    except:
        days = 7
    
    print(f"{Colors.CYAN}Период анализа: {days} дней{Colors.END}\n")
    
    # Получаем события
    events = get_events(days)
    
    if not events:
        print(f"{Colors.RED}❌ Нет событий за указанный период{Colors.END}")
        input("\nНажмите Enter для выхода...")
        return
    
    # Анализируем
    analysis = analyze_events(events)
    
    # Генерируем отчет
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    output_file = f"C:\\SecurityAnalysis_CVE_{timestamp}.html"
    report_file = generate_html_report(analysis, days, output_file)
    
    # Выводим результаты в консоль
    print(f"\n{Colors.YELLOW}📊 Результаты:{Colors.END}")
    print(f"   Всего событий: {Colors.CYAN}{analysis['total_events']}{Colors.END}")
    print(f"   Уникальных типов: {Colors.CYAN}{analysis['unique_types']}{Colors.END}")
    print(f"   Критических событий: {Colors.RED}{analysis['critical_count']}{Colors.END}")
    
    # Информация о CVE
    cve_count = sum(len(event['cves']) for event in analysis['critical_events_with_subjects'])
    print(f"   Связанных CVE: {Colors.MAGENTA}{cve_count}{Colors.END}")
    
    print(f"\n{Colors.MAGENTA}🔝 Топ-10 самых частых событий:{Colors.END}")
    top_events = sorted([e for e in analysis['detailed'] if e['count'] > 0], 
                       key=lambda x: x['count'], reverse=True)[:10]
    for event in top_events:
        cve_indicator = " ⚠️" if event['cves'] else ""
        print(f"   [{event['id']}] {event['description']}: {Colors.GREEN}{event['count']}{Colors.END}{cve_indicator}")
    
    # Информация о критических событиях
    if analysis['critical_events_with_subjects']:
        print(f"\n{Colors.RED}🔴 Критические события с анализом:{Colors.END}")
        for critical in analysis['critical_events_with_subjects'][:5]:
            subjects = critical['subjects']
            print(f"   [{critical['event'].EventID}] {critical['info']['desc']}")
            if subjects['SubjectUserName']:
                print(f"      User: {subjects['SubjectUserName']}")
            if subjects['IpAddress'] and subjects['IpAddress'] not in ['-', '::']:
                print(f"      IP: {subjects['IpAddress']}")
            if critical['cves']:
                cve_list = ', '.join(cve['id'] for cve in critical['cves'])
                print(f"      CVE: {cve_list}")
    
    # Открываем в браузере
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
    
    input(f"\n{Colors.GREEN}========================================{Colors.END}\nНажмите Enter для выхода...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Операция отменена пользователем{Colors.END}")
        time.sleep(2)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Критическая ошибка: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")