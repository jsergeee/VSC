#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Генератор HTML отчетов для анализа событий безопасности
"""

import time
from collections import defaultdict
from utils import escape_html, Colors
from event_database import get_level_color
from css_style import CSS_STYLE

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
        categories.append({
            'name': cat,
            'total': data['total'],
            'types': len(data['types']),
            'critical': data['critical'],
            'percentage': percentage
        })
    categories.sort(key=lambda x: x['total'], reverse=True)
    
    # Проверяем наличие данных о пользователях
    has_user_data = bool(analysis.get('user_logon_stats') or analysis.get('user_failed_logons') or analysis.get('privileged_users'))
    
    # Создание HTML
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Полный анализ событий безопасности Windows с CVE</title>
    <style>
        {CSS_STYLE}
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
                <div class="number">{analysis.get('critical_count', 0)}</div>
                <div class="label">Критических событий</div>
            </div>
            <div class="stat-card">
                <div class="number">{analysis.get('total_unique_users', 0)}</div>
                <div class="label">Уникальных пользователей</div>
            </div>
            <div class="stat-card">
                <div class="number">{analysis.get('total_failed_users', 0)}</div>
                <div class="label">Пользователей с ошибками</div>
            </div>
        </div>
        
        <div class="cve-section">
            <h2>⚠️ CVE Уязвимости, связанные с событиями</h2>
            <div class="cve-grid">
"""
    
    # Добавляем уникальные CVE из критических событий
    cve_set = set()
    for event in analysis.get('critical_events_with_subjects', []):
        for cve in event.get('cves', []):
            cve_key = cve.get('id', '')
            if cve_key and cve_key not in cve_set:
                cve_set.add(cve_key)
                html += f"""
                <div class="cve-item">
                    <div class="cve-id">{cve.get('id', 'N/A')}</div>
                    <div class="cve-desc">{escape_html(cve.get('description', 'Нет описания'))}</div>
                    <div><span class="cve-severity">{cve.get('severity', 'Unknown')}</span></div>
                    <div class="cve-remediation">🔧 {escape_html(cve.get('remediation', 'Нет рекомендаций'))}</div>
                </div>
"""
    
    if not cve_set:
        html += "<p class='empty-state'>Нет связанных CVE уязвимостей</p>"
    
    html += f"""
            </div>
        </div>
        
         <!-- Новая секция: Статистика пользователей -->
        <div class="user-stats">
            <h2>👥 Расширенный анализ учетных записей</h2>
            <div class="stats-grid">
                <!-- Топ успешных входов -->
                <div class="stats-card">
                    <h3>📈 Топ пользователей по успешным входам (событие 4624)</h3>
                    <ul class="stats-list">
"""
    
    # Топ успешных входов - показываем всех пользователей
    if analysis.get('user_logon_stats'):
        for user, count in list(analysis['user_logon_stats'].items())[:15]:
            html += f"""
                        <li>
                            <span class="user-name">{escape_html(user)}</span>
                            <span class="user-count">{count}</span>
                        </li>"""
    else:
        html += "<li class='empty-state'>Нет данных о входах пользователей</li>"
    
    html += f"""
                    </ul>
                </div>
                
                <!-- Топ неудачных входов -->
                <div class="stats-card">
                    <h3>⚠️ Топ пользователей с неудачными входами (событие 4625)</h3>
                    <ul class="stats-list">
"""
    
    if analysis.get('user_failed_logons'):
        for user, count in list(analysis['user_failed_logons'].items())[:15]:
            html += f"""
                        <li>
                            <span class="user-name">{escape_html(user)}</span>
                            <span class="failed-count">{count}</span>
                        </li>"""
    else:
        html += "<li class='empty-state'>Нет неудачных попыток входа</li>"
    
    html += f"""
                    </ul>
                </div>
                
                <!-- Пользователи с привилегиями -->
                <div class="stats-card">
                    <h3>👑 Пользователи со специальными привилегиями (событие 4672)</h3>
                    <ul class="stats-list">
"""
    
    if analysis.get('privileged_users'):
        for user in sorted(analysis['privileged_users'])[:15]:
            html += f"""
                        <li>
                            <span class="user-name">{escape_html(user)}</span>
                        </li>"""
        if len(analysis['privileged_users']) > 15:
            html += f"<li>... и еще {len(analysis['privileged_users']) - 15} пользователей</li>"
    else:
        html += "<li class='empty-state'>Нет пользователей со спец. привилегиями</li>"
    
    html += f"""
                    </ul>
                </div>
            </div>
        </div>
        
        <!-- Новая секция: Типы входов и временной анализ -->
        <div class="time-analysis">
            <h2>⏰ Анализ активности входа в систему</h2>
            <div class="stats-grid">
                <!-- Типы входов -->
                <div class="stats-card">
                    <h3>🔑 Статистика по типам входов</h3>
                    <ul class="stats-list">
"""
    
    logon_type_desc = {
        "2": "Интерактивный (локальный)",
        "3": "Сетевой (сетевые ресурсы)",
        "4": "Пакетный (задачи)",
        "5": "Сервис (службы)",
        "7": "Разблокировка",
        "8": "Сетевой с явными данными",
        "9": "NewCredentials (RunAs)",
        "10": "Удаленный (RDP)",
        "11": "Кэшированный интерактивный"
    }
    
    if analysis.get('logon_types'):
        for logon_type, count in sorted(analysis['logon_types'].items(), key=lambda x: x[1], reverse=True):
            desc = logon_type_desc.get(logon_type, f"Неизвестный тип ({logon_type})")
            type_class = f"logon-type-{logon_type}" if logon_type in logon_type_desc else ""
            html += f"""
                        <li>
                            <span><span class="logon-type-badge {type_class}">{desc}</span></span>
                            <span class="user-count">{count}</span>
                        </li>"""
    else:
        html += "<li class='empty-state'>Нет данных о типах входов</li>"
    
    html += f"""
                    </ul>
                </div>
                
                <!-- Активность по часам -->
                <div class="stats-card">
                    <h3>📊 Распределение входов по часам</h3>
                    <div class="time-chart">
"""
    
    if analysis.get('logon_hours'):
        max_count = max(analysis['logon_hours'].values()) if analysis['logon_hours'] else 1
        for hour in range(24):
            count = analysis['logon_hours'].get(hour, 0)
            height = (count / max_count * 200) if max_count > 0 else 0
            html += f"""
                        <div class="time-bar" style="height: {height}px;" data-count="{count}" title="Час {hour}:00 - {count} входов"></div>"""
    else:
        html += "<p class='empty-state'>Нет данных о временной активности</p>"
    
    html += f"""
                    </div>
                    <div class="time-label">
                        <span>00:00</span>
                        <span>06:00</span>
                        <span>12:00</span>
                        <span>18:00</span>
                        <span>23:00</span>
                    </div>
                </div>
                
                <!-- Последние изменения учетных записей -->
                <div class="stats-card">
                    <h3>📝 Последние изменения учетных записей</h3>
                    <ul class="stats-list">
"""
    
    if analysis.get('account_changes'):
        for change in analysis['account_changes'][-10:]:
            time_str = change['timestamp'].strftime('%H:%M %d.%m') if hasattr(change['timestamp'], 'strftime') else str(change['timestamp'])
            if change['username'] and change['username'] not in ['-']:
                html += f"""
                        <li>
                            <span class="user-name">{escape_html(change['username'])}</span>
                            <span class="user-count" style="background: #95a5a6;">{time_str}</span>
                        </li>"""
    else:
        html += "<li class='empty-state'>Нет изменений учетных записей</li>"
    
    html += f"""
                    </ul>
                </div>
            </div>
        </div>
        
        <!-- Новая секция: Анализ привилегий -->
        <div class="privilege-stats">
            <h2>🔐 Детальный анализ привилегий</h2>
            <div class="stats-grid">
                <div class="stats-card">
                    <h3>⚠️ Особо опасные привилегии (высокий риск)</h3>
"""
    
    # Анализ привилегий из критических событий
    dangerous_privileges_detected = set()
    all_privileges = []
    
    # Собираем привилегии из событий
    for event in analysis.get('critical_events_with_subjects', []):
        if event['event'].EventID == 4672 and event['subjects'].get('Privileges_detail'):
            all_privileges.extend(event['subjects']['Privileges_detail'])
            for priv in event['subjects']['Privileges_detail']:
                if priv.get('risk') == 'Высокий':
                    dangerous_privileges_detected.add(priv['name'])
    
    dangerous_privileges = {
        "SeTcbPrivilege": "Работа как часть ОС - позволяет олицетворять любого пользователя",
        "SeDebugPrivilege": "Отладка программ - доступ к процессам других пользователей",
        "SeTakeOwnershipPrivilege": "Владение объектами - стать владельцем любого объекта",
        "SeLoadDriverPrivilege": "Загрузка драйверов - загрузка вредоносных драйверов",
        "SeBackupPrivilege": "Резервное копирование - чтение любых файлов",
        "SeRestorePrivilege": "Восстановление - запись любых файлов",
        "SeCreateTokenPrivilege": "Создание токенов - создание токенов с любыми привилегиями",
        "SeIncreaseQuotaPrivilege": "Увеличение квот - повышение привилегий",
        "SeSystemEnvironmentPrivilege": "Изменение параметров среды - доступ к прошивке",
        "SeShutdownPrivilege": "Завершение работы - возможность DoS"
    }
    
    for priv_name, priv_desc in dangerous_privileges.items():
        detected = priv_name in dangerous_privileges_detected
        detected_class = "style='border-left: 4px solid #27ae60;'" if detected else ""
        html += f"""
                    <div class="privilege-item privilege-high" {detected_class}>
                        <div class="privilege-name">{priv_name} {'' if not detected else '✓'}</div>
                        <div class="privilege-desc">{priv_desc}</div>
                        <span class="privilege-risk risk-high">{'Обнаружено' if detected else 'Высокий риск'}</span>
                    </div>"""
    
    html += f"""
                </div>
                
                <div class="stats-card">
                    <h3>📋 Обнаруженные привилегии в событиях 4672</h3>
"""
    
    if all_privileges:
        # Группируем по риску
        high_risk = [p for p in all_privileges if p.get('risk') == 'Высокий']
        medium_risk = [p for p in all_privileges if p.get('risk') == 'Средний']
        
        if high_risk:
            html += "<h4 style='color: #e74c3c; margin: 15px 0 10px 0;'>Высокий риск:</h4>"
            for priv in high_risk[:10]:
                html += f"""
                    <div class="privilege-item privilege-high">
                        <div class="privilege-name">{priv['name']}</div>
                        <div class="privilege-desc">{priv['description']}</div>
                    </div>"""
        
        if medium_risk:
            html += "<h4 style='color: #f39c12; margin: 15px 0 10px 0;'>Средний риск:</h4>"
            for priv in medium_risk[:10]:
                html += f"""
                    <div class="privilege-item privilege-medium">
                        <div class="privilege-name">{priv['name']}</div>
                        <div class="privilege-desc">{priv['description']}</div>
                    </div>"""
        
        if len(high_risk) + len(medium_risk) > 20:
            html += f"<p>... и еще {len(high_risk) + len(medium_risk) - 20} привилегий</p>"
    else:
        html += "<p class='empty-state'>Не обнаружено событий с детальным анализом привилегий</p>"
    
    html += f"""
                </div>
            </div>
        </div>
        
        <!-- Новая секция: Сетевой анализ -->
        <div class="ip-stats">
            <h2>🌐 Сетевой анализ источников подключений</h2>
            <div class="stats-grid">
                <!-- Топ IP адресов -->
                <div class="stats-card">
                    <h3>📍 Топ IP адресов источников</h3>
                    <ul class="stats-list">
"""
    
    if analysis.get('source_ips'):
        for ip, count in list(analysis['source_ips'].items())[:20]:
            # Определяем тип IP для стилизации
            ip_type = "public"
            ip_type_display = "Внешний"
            
            if ip in ['127.0.0.1', '::1', 'localhost']:
                ip_type = "loopback"
                ip_type_display = "Локальный"
            elif ip.startswith(('10.', '192.168.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', 
                               '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', 
                               '172.28.', '172.29.', '172.30.', '172.31.')):
                ip_type = "private"
                ip_type_display = "Приватный"
            
            html += f"""
                        <li>
                            <span class="ip-address">
                                {escape_html(ip)} 
                                <span class="ip-type ip-{ip_type}">{ip_type_display}</span>
                            </span>
                            <span class="user-count">{count}</span>
                        </li>"""
    else:
        html += "<li class='empty-state'>Нет данных об IP адресах</li>"
    
    html += f"""
                    </ul>
                </div>
                
                <!-- Детальный анализ IP -->
                <div class="stats-card">
                    <h3>📊 Статистика по типам IP адресов</h3>
"""
    
    if analysis.get('source_ips'):
        # Подсчет статистики по типам IP
        ip_stats = {'private': 0, 'public': 0, 'loopback': 0, 'total': 0}
        for ip in analysis['source_ips'].keys():
            if ip in ['127.0.0.1', '::1', 'localhost']:
                ip_stats['loopback'] += 1
            elif ip.startswith(('10.', '192.168.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', 
                               '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', 
                               '172.28.', '172.29.', '172.30.', '172.31.')):
                ip_stats['private'] += 1
            else:
                ip_stats['public'] += 1
            ip_stats['total'] += 1
        
        html += f"""
                    <ul class="stats-list">
                        <li>
                            <span>🌍 Внешние публичные IP</span>
                            <span class="user-count" style="background: #e74c3c;">{ip_stats['public']}</span>
                        </li>
                        <li>
                            <span>🏠 Приватные IP (локальная сеть)</span>
                            <span class="user-count" style="background: #f39c12;">{ip_stats['private']}</span>
                        </li>
                        <li>
                            <span>💻 Локальные (localhost)</span>
                            <span class="user-count" style="background: #7f8c8d;">{ip_stats['loopback']}</span>
                        </li>
                        <li>
                            <span>📊 Всего уникальных IP</span>
                            <span class="user-count" style="background: #3498db;">{ip_stats['total']}</span>
                        </li>
                    </ul>"""
    else:
        html += "<p class='empty-state'>Нет данных для анализа</p>"
    
    html += f"""
                </div>
            </div>
        </div>
        
        <!-- Секция с критическими событиями -->
        <div class="critical-events">
            <h2>🔴 Критические события с детальным анализом субъектов</h2>
            <div class="critical-grid">
"""
    
    # Добавляем критические события с анализом субъектов
    if analysis.get('critical_events_with_subjects'):
        for critical in analysis['critical_events_with_subjects'][:10]:  # Показываем топ-10 критических
            event_time = critical['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(critical['timestamp'], 'strftime') else str(critical['timestamp'])
            subjects = critical['subjects']
            
            html += f"""
                <div class="critical-item">
                    <div class="critical-header">
                        <span class="critical-id">Событие {critical['event'].EventID}</span>
                        <span class="critical-time">{event_time}</span>
                    </div>
                    <div class="event-description">
                        <strong>📌 Описание:</strong> {escape_html(critical['info']['desc'])}
                    </div>
                    
                    <div class="event-details">
                        <!-- Секция Субъект (кто запросил вход) -->
                        <div class="detail-section">
                            <h4>👤 Субъект (инициатор)</h4>
                            <div class="detail-grid">
                                <span class="detail-label">ИД безопасности:</span>
                                <span class="detail-value">{escape_html(subjects.get('SubjectUserSid', 'Не указан'))}</span>
                                
                                <span class="detail-label">Имя учетной записи:</span>
                                <span class="detail-value">{escape_html(subjects.get('SubjectUserName', 'Не указан'))}</span>
                                
                                <span class="detail-label">Домен учетной записи:</span>
                                <span class="detail-value">{escape_html(subjects.get('SubjectDomainName', 'Не указан'))}</span>
                                
                                <span class="detail-label">ИД входа:</span>
                                <span class="detail-value">{escape_html(subjects.get('SubjectLogonId', 'Не указан'))}</span>
                            </div>
                        </div>
                        
                        <!-- Секция сведений о входе -->
                        <div class="detail-section">
                            <h4>🔑 Сведения о входе</h4>
                            <div class="detail-grid">
                                <span class="detail-label">Тип входа:</span>
                                <span class="detail-value">
                                    {escape_html(subjects.get('LogonType', 'Не указан'))}
                                    {f"<span class='logon-type-badge logon-type-{subjects.get('LogonType', '')}'>{escape_html(subjects.get('LogonTypeDesc', ''))}</span>" if subjects.get('LogonTypeDesc') else ''}
                                </span>
                                
                                <span class="detail-label">Ограниченный режим администрирования:</span>
                                <span class="detail-value">{escape_html(subjects.get('AdminMode', '-'))}</span>
                                
                                <span class="detail-label">Виртуальная учетная запись:</span>
                                <span class="detail-value">{escape_html(subjects.get('VirtualAccount', 'Нет'))}</span>
                                
                                <span class="detail-label">Расширенный маркер:</span>
                                <span class="detail-value">{escape_html(subjects.get('ElevatedToken', 'Да'))}</span>
                                
                                <span class="detail-label">Уровень олицетворения:</span>
                                <span class="detail-value">{escape_html(subjects.get('ImpersonationLevel', 'Олицетворение'))}</span>
                            </div>
                        </div>
                        
                        <!-- Секция Новый вход (целевая учетная запись) -->
                        <div class="detail-section">
                            <h4>🎯 Новый вход (целевая учетная запись)</h4>
                            <div class="detail-grid">
                                <span class="detail-label">ИД безопасности:</span>
                                <span class="detail-value">{escape_html(subjects.get('TargetUserSid', 'Не указан'))}</span>
                                
                                <span class="detail-label">Имя учетной записи:</span>
                                <span class="detail-value">{escape_html(subjects.get('TargetUserName', 'Не указан'))}</span>
                                
                                <span class="detail-label">Домен учетной записи:</span>
                                <span class="detail-value">{escape_html(subjects.get('TargetDomainName', 'Не указан'))}</span>
                                
                                <span class="detail-label">ИД входа:</span>
                                <span class="detail-value">{escape_html(subjects.get('TargetLogonId', 'Не указан'))}</span>
                                
                                <span class="detail-label">Связанный ИД входа:</span>
                                <span class="detail-value">{escape_html(subjects.get('LinkedLogonId', '0x0'))}</span>
                                
                                <span class="detail-label">Сетевое имя учетной записи:</span>
                                <span class="detail-value">{escape_html(subjects.get('NetworkAccountName', '-'))}</span>
                                
                                <span class="detail-label">Сетевой домен учетной записи:</span>
                                <span class="detail-value">{escape_html(subjects.get('NetworkAccountDomain', '-'))}</span>
                                
                                <span class="detail-label">GUID входа:</span>
                                <span class="detail-value">{escape_html(subjects.get('Guid', '{00000000-0000-0000-0000-000000000000}'))}</span>
                            </div>
                        </div>
                        
                        <!-- Секция сведений о процессе -->
                        <div class="detail-section">
                            <h4>⚙️ Сведения о процессе</h4>
                            <div class="process-info">
                                <div><strong>ИД процесса:</strong> {escape_html(subjects.get('ProcessId', 'Не указан'))}</div>
                                <div><strong>Имя процесса:</strong> {escape_html(subjects.get('ProcessName', 'Не указан'))}</div>
                            </div>
                        </div>
                        
                        <!-- Секция сетевых сведений -->
                        <div class="detail-section">
                            <h4>🌐 Сведения о сети</h4>
                            <div class="detail-grid">
                                <span class="detail-label">Имя рабочей станции:</span>
                                <span class="detail-value">{escape_html(subjects.get('WorkstationName', '-'))}</span>
                                
                                <span class="detail-label">Сетевой адрес источника:</span>
                                <span class="detail-value">
                                    {escape_html(subjects.get('IpAddress', '-'))}
                                    {f"<span class='ip-type ip-{subjects['IpAnalysis'].get('type', 'unknown')}'>{subjects['IpAnalysis'].get('type', '')}</span>" if subjects.get('IpAnalysis') else ''}
                                </span>
                                
                                <span class="detail-label">Порт источника:</span>
                                <span class="detail-value">{escape_html(subjects.get('IpPort', '-'))}</span>
                            </div>
                        </div>
                        
                        <!-- Секция подробных сведений о проверке подлинности -->
                        <div class="detail-section">
                            <h4>🔐 Подробные сведения о проверке подлинности</h4>
                            <div class="auth-info">
                                <div class="detail-grid">
                                    <span class="detail-label">Процесс входа:</span>
                                    <span class="detail-value">{escape_html(subjects.get('LogonProcess', 'Advapi'))}</span>
                                    
                                    <span class="detail-label">Пакет проверки подлинности:</span>
                                    <span class="detail-value">{escape_html(subjects.get('AuthenticationPackage', 'Negotiate'))}</span>
                                    
                                    <span class="detail-label">Промежуточные службы:</span>
                                    <span class="detail-value">{escape_html(subjects.get('TransmittedServices', '-'))}</span>
                                    
                                    <span class="detail-label">Имя пакета (NTLM):</span>
                                    <span class="detail-value">{escape_html(subjects.get('PackageName', '-'))}</span>
                                    
                                    <span class="detail-label">Длина ключа:</span>
                                    <span class="detail-value">{escape_html(subjects.get('KeyLength', '0'))}</span>
                                </div>
                            </div>
                        </div>
"""
            
            # Добавляем анализ SID если есть
            if subjects.get('SidAnalysis'):
                sid_info = subjects['SidAnalysis']
                sid_warning = "⚠️" if sid_info.get('well_known') else ""
                html += f"""
                        <div class="detail-section">
                            <h4>🔍 Анализ безопасности {sid_warning}</h4>
                            <div class="detail-grid">
                                <span class="detail-label">Тип SID:</span>
                                <span class="detail-value">{escape_html(sid_info.get('type', 'Неизвестно'))}</span>
                                
                                <span class="detail-label">Описание:</span>
                                <span class="detail-value">{escape_html(sid_info.get('description', 'Нет описания'))}</span>
                                
                                <span class="detail-label">Well-Known:</span>
                                <span class="detail-value">{'Да' if sid_info.get('well_known') else 'Нет'}</span>
                            </div>
                        </div>"""
            
            # Добавляем анализ привилегий если есть
            if subjects.get('Privileges_detail'):
                html += f"""
                        <div class="detail-section">
                            <h4>⚡ Назначенные привилегии</h4>"""
                for priv in subjects['Privileges_detail']:
                    risk_class = "risk-high" if priv.get('risk') == 'Высокий' else "risk-medium"
                    html += f"""
                            <div class="privilege-item privilege-{'high' if priv.get('risk') == 'Высокий' else 'medium'}">
                                <div class="privilege-name">{priv['name']}</div>
                                <div class="privilege-desc">{priv['description']}</div>
                                <span class="privilege-risk {risk_class}">{priv.get('risk', 'Средний')}</span>
                            </div>"""
                html += f"""
                        </div>"""
            
            # Добавляем CVE для этого события
            if critical.get('cves'):
                html += f"""
                        <div class="detail-section">
                            <h4>⚠️ Связанные уязвимости (CVE)</h4>
                            <div class="cve-container">"""
                for cve in critical['cves']:
                    html += f"""
                                <div class="cve-item">
                                    <div class="cve-id">{cve.get('id', 'N/A')}</div>
                                    <div class="cve-desc">{escape_html(cve.get('description', 'Нет описания'))}</div>
                                    <span class="cve-severity">{cve.get('severity', 'Unknown')}</span>
                                </div>"""
                html += f"""
                            </div>
                        </div>"""
            
            html += f"""
                    </div>
                </div>
"""
    else:
        html += "<p class='empty-state'>Нет критических событий за указанный период</p>"
    
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
        if event.get('cves'):
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
            <p>🔄 Версия анализатора: 3.15 (с расширенным анализом УЗ, привилегий и сети)</p>
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