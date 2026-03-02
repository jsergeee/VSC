def analyze_events(events):
    """Анализ событий с расширенной статистикой по УЗ"""
    print(f"{Colors.CYAN}📈 Анализ событий...{Colors.END}")
    
    # Статистика по ID событий
    event_counter = Counter()
    critical_events_with_subjects = []
    
    # Дополнительная статистика
    user_logon_stats = defaultdict(int)  # Статистика входов по пользователям
    user_failed_logons = defaultdict(int)  # Неудачные входы по пользователям
    privileged_users = set()  # Пользователи с привилегиями
    logon_types = defaultdict(int)  # Типы входов
    logon_hours = defaultdict(int)  # Входы по часам
    source_ips = defaultdict(int)  # IP адреса источников
    account_changes = []  # Изменения учетных записей
    service_installs = []  # Установки служб
    scheduled_tasks = []  # Создание/изменение заданий
    
    # Множество для отслеживания уникальных пользователей
    unique_users = set()
    
    for event in events:
        event_id = event.EventID
        event_counter[event_id] += 1
        event_info = get_event_description(event_id)
        
        # Извлекаем субъекты для всех событий
        subjects = extract_subjects_from_event(event)
        
        # Специфичный анализ для разных типов событий
        if event_id == 4624:  # Успешный вход
            # Для 4624 используем TargetUserName
            username = subjects.get('TargetUserName')
            if username and username not in ['-', '']:  # Убираем только пустые и прочерки
                user_logon_stats[username] += 1
                unique_users.add(username)
                
                if subjects.get('LogonType'):
                    logon_types[subjects['LogonType']] += 1
                
                if subjects.get('IpAddress') and subjects['IpAddress'] not in ['-', '::', '127.0.0.1', 'localhost']:
                    source_ips[subjects['IpAddress']] += 1
                
                # Статистика по часам
                if hasattr(event.TimeGenerated, 'hour'):
                    logon_hours[event.TimeGenerated.hour] += 1
        
        elif event_id == 4625:  # Неудачный вход
            # Для 4625 также используем TargetUserName
            username = subjects.get('TargetUserName')
            if username and username not in ['-', '']:
                user_failed_logons[username] += 1
                unique_users.add(username)
        
        elif event_id == 4672:  # Специальные привилегии
            # Для 4672 используем SubjectUserName (кто получил привилегии)
            username = subjects.get('SubjectUserName')
            if username and username not in ['-', '']:
                privileged_users.add(username)
                unique_users.add(username)
                if subjects.get('PrivilegeList'):
                    subjects['Privileges_detail'] = analyze_privileges(subjects['PrivilegeList'])
        
        elif event_id == 4648:  # Явные учетные данные
            username = subjects.get('TargetUserName') or subjects.get('SubjectUserName')
            if username and username not in ['-', '']:
                unique_users.add(username)
        
        elif event_id in [4720, 4722, 4723, 4724, 4725, 4726, 4738, 4740, 4767]:  # Изменения УЗ
            username = subjects.get('TargetUserName') or subjects.get('SubjectUserName')
            if username and username not in ['-', '']:
                unique_users.add(username)
                account_changes.append({
                    'event_id': event_id,
                    'username': username,
                    'timestamp': event.TimeGenerated,
                    'description': event_info['desc']
                })
        
        elif event_id == 4697:  # Установка службы
            service_installs.append({
                'service_name': subjects.get('ServiceName', 'Unknown'),
                'username': subjects.get('SubjectUserName', 'Unknown'),
                'timestamp': event.TimeGenerated
            })
        
        elif event_id in [4698, 4699, 4700, 4701, 4702]:  # Задания планировщика
            scheduled_tasks.append({
                'event_id': event_id,
                'task_name': subjects.get('TaskName', 'Unknown'),
                'username': subjects.get('SubjectUserName', 'Unknown'),
                'timestamp': event.TimeGenerated
            })
        
        # Для критических событий собираем детальную информацию
        if event_info['level'] in ['Critical', 'Failure', 'Error']:
            cves = get_cve_for_event(event_id, event)
            
            critical_events_with_subjects.append({
                'event': event,
                'info': event_info,
                'subjects': subjects,
                'cves': cves,
                'timestamp': event.TimeGenerated
            })
    
    # Собираем все уникальные ID
    from event_database import EVENT_DATABASE
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
    
    # Топ пользователей по входам - теперь включаем всех, включая системные
    top_users = sorted(user_logon_stats.items(), key=lambda x: x[1], reverse=True)
    top_failed_users = sorted(user_failed_logons.items(), key=lambda x: x[1], reverse=True)
    top_ips = sorted(source_ips.items(), key=lambda x: x[1], reverse=True)
    
    # Для отладки - выведем информацию о найденных пользователях
    print(f"{Colors.GREEN}  Найдено уникальных пользователей: {len(unique_users)}{Colors.END}")
    if user_logon_stats:
        print(f"  Топ пользователей по входам: {dict(list(top_users)[:5])}")
    
    return {
        'detailed': detailed_stats,
        'category_stats': category_stats,
        'total_events': total_events,
        'unique_types': unique_types,
        'critical_count': critical_count,
        'critical_events_with_subjects': critical_events_with_subjects,
        'event_counter': event_counter,
        # Новая расширенная статистика - теперь включаем всех пользователей
        'user_logon_stats': dict(top_users),
        'user_failed_logons': dict(top_failed_users),
        'privileged_users': list(privileged_users),
        'logon_types': dict(logon_types),
        'logon_hours': dict(logon_hours),
        'source_ips': dict(top_ips),
        'account_changes': account_changes[-50:],  # Последние 50 изменений
        'service_installs': service_installs[-20:],  # Последние 20 установок служб
        'scheduled_tasks': scheduled_tasks[-30:],  # Последние 30 задач
        'total_unique_users': len(unique_users),
        'total_failed_users': len(user_failed_logons),
    }