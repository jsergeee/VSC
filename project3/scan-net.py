#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматический сканер сети для планировщика заданий
Версия: 1.1 (исправлена кодировка для Windows)
"""

import os
import sys
import json
import subprocess
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import configparser
import re


class AutoNetworkScanner:
    def __init__(self):
        # Определяем директории
        self.script_dir = Path(__file__).parent.absolute()
        self.results_dir = self.script_dir / "scan_results"
        self.logs_dir = self.script_dir / "logs"
        self.config_file = self.script_dir / "scanner_config.ini"
        
        # Создаем директории
        self.results_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Настройка логгирования
        self.setup_logging()
        
        # Загрузка конфигурации
        self.config = self.load_config()
        
        # Таймстамп
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        
        self.logger.info("=" * 60)
        self.logger.info("АВТОМАТИЧЕСКИЙ СКАНЕР СЕТИ")
        self.logger.info(f"Запуск: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Директория: {self.script_dir}")
        self.logger.info("=" * 60)
    
    def setup_logging(self):
        """Настройка логгирования"""
        log_file = self.logs_dir / f"scanner_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self):
        """Загрузка конфигурации"""
        config = configparser.ConfigParser()
        
        # Значения по умолчанию
        defaults = {
            'Scanner': {
                'networks': '192.168.252.0/24',
                'scan_types': 'basic,netbios,smb',
                'output_formats': 'txt,json',
                'retention_days': '30',
                'max_scan_time': '1800',
                'scan_interval_hours': '24',
            },
            'Nmap': {
                'path': 'nmap',
                'timeout': '30',
                'max_retries': '2',
            },
            'Network': {
                'auto_detect': 'true',
                'skip_virtual_adapters': 'true',
            }
        }
        
        if self.config_file.exists():
            config.read(self.config_file, encoding='utf-8')
            self.logger.info(f"Конфигурация загружена из {self.config_file}")
        else:
            config.read_dict(defaults)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            self.logger.info(f"Создан файл конфигурации {self.config_file}")
        
        return config
    
    def check_nmap(self):
        """Проверка наличия nmap"""
        try:
            nmap_path = self.config.get('Nmap', 'path', fallback='nmap')
            result = subprocess.run(
                [nmap_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',  # Версия nmap обычно на английском
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                self.logger.info(f"Nmap найден: {version}")
                return True
            else:
                self.logger.error(f"Nmap не работает: {result.stderr}")
                return False
                
        except FileNotFoundError:
            self.logger.error("Nmap не установлен!")
            self.logger.error("Установите: https://nmap.org/download.html")
            return False
        except Exception as e:
            self.logger.error(f"Ошибка проверки nmap: {e}")
            return False
    
    def decode_output(self, bytes_output):
        """Декодирование вывода с учетом русской кодировки Windows"""
        try:
            # Сначала пробуем utf-8
            return bytes_output.decode('utf-8')
        except UnicodeDecodeError:
            try:
                # Потом cp866 (русская DOS)
                return bytes_output.decode('cp866')
            except UnicodeDecodeError:
                # Если не получается, пробуем latin-1
                return bytes_output.decode('latin-1', errors='replace')
    
    def get_local_networks(self):
        """Получение локальных сетей"""
        networks = []
        
        # Сети из конфигурации
        config_networks = self.config.get('Scanner', 'networks', fallback='')
        if config_networks:
            for net in config_networks.split(','):
                net = net.strip()
                if net:
                    networks.append({
                        'cidr': net,
                        'source': 'config'
                    })
        
        # Автоматическое определение (если включено)
        if self.config.getboolean('Network', 'auto_detect', fallback=True):
            try:
                # Используем ipconfig для Windows
                result = subprocess.run(
                    ['ipconfig'],
                    capture_output=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    # Декодируем с учетом русской кодировки
                    output = self.decode_output(result.stdout)
                    
                    # Парсим вывод ipconfig
                    lines = output.split('\n')
                    current_adapter = None
                    current_ip = None
                    
                    for line in lines:
                        line = line.strip()
                        
                        # Имя адаптера
                        if 'адаптер' in line.lower() and ':' in line:
                            current_adapter = line.split(':')[0].strip()
                            current_ip = None
                        
                        # IPv4 адрес
                        elif ('ipv4' in line.lower() or 
                              'адрес ip' in line.lower() or 
                              'ip address' in line.lower()):
                            # Ищем IPv4 адрес
                            match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                            if match:
                                ip = match.group(1)
                                current_ip = ip
                                
                                # Пропускаем специальные адреса
                                if (ip.startswith('127.') or 
                                    ip.startswith('169.254.') or
                                    ip.startswith('172.24.') or
                                    ip.startswith('172.29.') or
                                    ip.startswith('172.21.') or
                                    ip.startswith('172.20.')):
                                    continue
                        
                        # Маска подсети
                        elif ('маска подсети' in line.lower() or 
                              'subnet mask' in line.lower()) and current_ip:
                            # Ищем маску
                            match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                            if match and current_adapter and current_ip:
                                mask = match.group(1)
                                
                                try:
                                    # Преобразуем в CIDR
                                    cidr = sum(bin(int(x)).count('1') for x in mask.split('.'))
                                    network_parts = current_ip.split('.')
                                    mask_parts = mask.split('.')
                                    
                                    # Вычисляем сеть
                                    network_parts = [
                                        str(int(network_parts[i]) & int(mask_parts[i]))
                                        for i in range(4)
                                    ]
                                    network_addr = '.'.join(network_parts)
                                    network_cidr = f"{network_addr}/{cidr}"
                                    
                                    # Проверяем, нет ли уже такой сети
                                    if not any(n['cidr'] == network_cidr for n in networks):
                                        networks.append({
                                            'cidr': network_cidr,
                                            'source': 'auto',
                                            'adapter': current_adapter,
                                            'ip': current_ip,
                                            'mask': mask
                                        })
                                except Exception as e:
                                    self.logger.debug(f"Ошибка вычисления сети: {e}")
                                        
            except Exception as e:
                self.logger.warning(f"Ошибка автоматического определения сетей: {e}")
        
        # Удаляем дубликаты
        unique_networks = []
        seen = set()
        for net in networks:
            if net['cidr'] not in seen:
                seen.add(net['cidr'])
                unique_networks.append(net)
        
        return unique_networks
    
    def run_scan(self, target, scan_type):
        """Выполнение сканирования"""
        nmap_path = self.config.get('Nmap', 'path', fallback='nmap')
        timeout = int(self.config.get('Nmap', 'timeout', fallback=30))
        max_retries = int(self.config.get('Nmap', 'max_retries', fallback=2))
        
        # Команды для разных типов сканирования
        commands = {
            'basic': [nmap_path, '-sn', '-T4', target],
            'netbios': [nmap_path, '-sU', '-p137', '--script', 'nbstat.nse', '-T4', target],
            'smb': [nmap_path, '-p139,445', '--script', 'smb-os-discovery', '-T4', target],
            'tcp_quick': [nmap_path, '-sS', '-sV', '--top-ports', '100', '-T4', target],
        }
        
        if scan_type not in commands:
            self.logger.error(f"Неизвестный тип сканирования: {scan_type}")
            return None, None, -1
        
        command = commands[scan_type]
        
        # Пытаемся выполнить сканирование с повторными попытками
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Сканирование {target} ({scan_type}), попытка {attempt + 1}")
                
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                try:
                    stdout_bytes, stderr_bytes = process.communicate(timeout=timeout)
                    
                    # Декодируем вывод
                    stdout = self.decode_output(stdout_bytes) if stdout_bytes else ""
                    stderr = self.decode_output(stderr_bytes) if stderr_bytes else ""
                    
                    if process.returncode == 0:
                        self.logger.info(f"Сканирование {target} завершено успешно")
                        return stdout, stderr, process.returncode
                    else:
                        self.logger.warning(f"Сканирование {target} завершено с кодом {process.returncode}")
                        if attempt == max_retries - 1:  # Последняя попытка
                            return stdout, stderr, process.returncode
                        else:
                            time.sleep(5)  # Ждем перед повторной попыткой
                            
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout_bytes, stderr_bytes = process.communicate()
                    stdout = self.decode_output(stdout_bytes) if stdout_bytes else ""
                    stderr = self.decode_output(stderr_bytes) if stderr_bytes else ""
                    self.logger.error(f"Таймаут сканирования {target}")
                    return stdout, stderr, -1
                    
            except Exception as e:
                self.logger.error(f"Ошибка сканирования {target}: {e}")
                if attempt == max_retries - 1:
                    return "", str(e), -1
        
        return None, None, -1
    
    def save_results(self, output, target, scan_type):
        """Сохранение результатов"""
        if not output:
            return []
        
        safe_target = target.replace('/', '_').replace(':', '_')
        base_name = f"{self.date_str}_{safe_target}_{scan_type}"
        
        saved_files = []
        formats = [f.strip() for f in 
                  self.config.get('Scanner', 'output_formats', fallback='txt').split(',')]
        
        # Сохранение в текстовом формате
        if 'txt' in formats:
            txt_file = self.results_dir / f"{base_name}.txt"
            try:
                with open(txt_file, 'w', encoding='utf-8') as f:
                    f.write(f"Сканирование сети\n")
                    f.write(f"Дата: {self.date_str}\n")
                    f.write(f"Время: {datetime.now().strftime('%H:%M:%S')}\n")
                    f.write(f"Цель: {target}\n")
                    f.write(f"Тип: {scan_type}\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(output)
                
                saved_files.append(str(txt_file))
                self.logger.info(f"Сохранен TXT: {txt_file.name}")
            except Exception as e:
                self.logger.error(f"Ошибка сохранения TXT: {e}")
        
        # Сохранение в JSON формате
        if 'json' in formats:
            json_file = self.results_dir / f"{base_name}.json"
            try:
                # Парсим результаты в JSON
                parsed_data = self.parse_to_json(output, target, scan_type)
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(parsed_data, f, indent=2, ensure_ascii=False, default=str)
                
                saved_files.append(str(json_file))
                self.logger.info(f"Сохранен JSON: {json_file.name}")
            except Exception as e:
                self.logger.error(f"Ошибка сохранения JSON: {e}")
        
        return saved_files
    
    def parse_to_json(self, text_output, target, scan_type):
        """Парсинг текстового вывода в JSON"""
        result = {
            'scan_info': {
                'target': target,
                'scan_type': scan_type,
                'timestamp': datetime.now().isoformat(),
                'date': self.date_str
            },
            'hosts': [],
            'summary': {
                'total_hosts': 0,
                'scan_duration': 'N/A'
            }
        }
        
        # Простой парсинг для basic scan
        if scan_type == 'basic':
            lines = text_output.split('\n')
            for line in lines:
                if 'Nmap scan report for' in line:
                    # Пример: Nmap scan report for 192.168.252.1
                    parts = line.split('for ')[1].strip()
                    host_info = {
                        'address': parts.split()[0] if ' ' in parts else parts,
                        'hostname': parts.split()[1] if ' ' in parts else None,
                        'status': 'up'
                    }
                    result['hosts'].append(host_info)
        
        # Парсинг для netbios scan
        elif scan_type == 'netbios':
            lines = text_output.split('\n')
            current_host = None
            
            for line in lines:
                line = line.strip()
                
                if 'Nmap scan report for' in line:
                    if current_host:
                        result['hosts'].append(current_host)
                    
                    parts = line.split('for ')[1].strip()
                    current_host = {
                        'address': parts.split()[0] if ' ' in parts else parts,
                        'hostname': parts.split()[1] if ' ' in parts else None,
                        'nbstat_info': {},
                        'ports': []
                    }
                
                elif 'MAC Address:' in line and current_host:
                    mac_parts = line.split('MAC Address:')[1].strip().split(' ')
                    if mac_parts:
                        current_host['mac'] = mac_parts[0]
                        if len(mac_parts) > 1:
                            current_host['vendor'] = ' '.join(mac_parts[1:]).strip('()')
                
                elif 'nbstat:' in line and current_host:
                    nb_info = line.split('nbstat:')[1].strip()
                    current_host['nbstat_info']['summary'] = nb_info
                
                elif 'Names:' in line and current_host:
                    pass  # Следующие строки будут именами
                
                elif line.startswith('  ') and current_host and 'nbstat_info' in current_host:
                    if '<' in line and '>' in line:
                        if 'names' not in current_host['nbstat_info']:
                            current_host['nbstat_info']['names'] = []
                        current_host['nbstat_info']['names'].append(line.strip())
                
                elif 'PORT' in line and 'STATE' in line and 'SERVICE' in line:
                    pass  # Заголовок таблицы портов
                
                elif '/udp' in line or '/tcp' in line:
                    port_parts = line.split()
                    if len(port_parts) >= 3 and current_host:
                        port_info = {
                            'port': port_parts[0],
                            'state': port_parts[1],
                            'service': port_parts[2]
                        }
                        current_host['ports'].append(port_info)
            
            if current_host:
                result['hosts'].append(current_host)
        
        result['summary']['total_hosts'] = len(result['hosts'])
        return result
    
    def cleanup_old_results(self):
        """Очистка старых результатов"""
        retention_days = int(self.config.get('Scanner', 'retention_days', fallback=30))
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        deleted = 0
        for file_path in self.results_dir.glob('*.*'):
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_date:
                    try:
                        file_path.unlink()
                        deleted += 1
                    except Exception as e:
                        self.logger.error(f"Ошибка удаления {file_path}: {e}")
        
        if deleted > 0:
            self.logger.info(f"Удалено старых файлов: {deleted}")
    
    def generate_summary(self, scan_results):
        """Генерация сводки"""
        summary_file = self.results_dir / f"summary_{self.date_str}.txt"
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"СВОДКА СКАНИРОВАНИЙ СЕТИ\n")
                f.write(f"Дата: {self.date_str}\n")
                f.write(f"Время генерации: {datetime.now().strftime('%H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                
                total_scans = len(scan_results)
                successful_scans = sum(1 for r in scan_results if r.get('success', False))
                
                f.write(f"Всего сканирований: {total_scans}\n")
                f.write(f"Успешных: {successful_scans}\n")
                f.write(f"Неудачных: {total_scans - successful_scans}\n\n")
                
                f.write("Детали по сканированиям:\n")
                f.write("-" * 60 + "\n")
                
                for result in scan_results:
                    status = "УСПЕШНО" if result.get('success') else "ОШИБКА"
                    f.write(f"Сеть: {result.get('target', 'N/A')}\n")
                    f.write(f"Тип: {result.get('scan_type', 'N/A')}\n")
                    f.write(f"Статус: {status}\n")
                    
                    files = result.get('files', [])
                    if files:
                        f.write(f"Файлы: {', '.join([Path(f).name for f in files])}\n")
                    
                    f.write("-" * 40 + "\n")
            
            self.logger.info(f"Сводка сохранена: {summary_file.name}")
            return str(summary_file)
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации сводки: {e}")
            return None
    
    def run(self):
        """Основной метод запуска"""
        self.logger.info("Запуск автоматического сканирования")
        
        # Проверка nmap
        if not self.check_nmap():
            self.logger.error("Nmap не найден. Завершение работы.")
            return False
        
        # Получение списка сетей
        networks = self.get_local_networks()
        if not networks:
            self.logger.error("Не найдено сетей для сканирования")
            return False
        
        self.logger.info(f"Найдено сетей: {len(networks)}")
        for net in networks:
            self.logger.info(f"  - {net['cidr']} ({net.get('source', 'unknown')})")
        
        # Типы сканирования
        scan_types = [t.strip() for t in 
                     self.config.get('Scanner', 'scan_types', fallback='basic').split(',')]
        
        # Результаты всех сканирований
        all_results = []
        
        # Выполнение сканирований
        for network in networks:
            target = network['cidr']
            
            for scan_type in scan_types:
                self.logger.info(f"Начало сканирования: {target} -> {scan_type}")
                
                start_time = time.time()
                stdout, stderr, returncode = self.run_scan(target, scan_type)
                elapsed_time = time.time() - start_time
                
                result_info = {
                    'target': target,
                    'scan_type': scan_type,
                    'success': returncode == 0,
                    'return_code': returncode,
                    'duration': f"{elapsed_time:.1f} сек",
                    'timestamp': datetime.now().isoformat()
                }
                
                # Сохранение результатов
                if stdout:
                    saved_files = self.save_results(stdout, target, scan_type)
                    result_info['files'] = saved_files
                    
                    if saved_files:
                        self.logger.info(f"Сканирование {target} ({scan_type}) завершено, сохранено файлов: {len(saved_files)}")
                    else:
                        self.logger.warning(f"Сканирование {target} завершено, но файлы не сохранены")
                else:
                    self.logger.warning(f"Нет результатов для {target} ({scan_type})")
                
                all_results.append(result_info)
                
                # Небольшая пауза между сканированиями
                time.sleep(2)
        
        # Генерация сводки
        if all_results:
            summary_file = self.generate_summary(all_results)
            if summary_file:
                self.logger.info(f"Итоговая сводка: {summary_file}")
        
        # Очистка старых результатов
        self.cleanup_old_results()
        
        self.logger.info("Автоматическое сканирование завершено")
        return True


def main():
    """Точка входа"""
    try:
        scanner = AutoNetworkScanner()
        success = scanner.run()
        
        # Возвращаем код выхода для планировщика
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nСканирование прервано")
        sys.exit(2)
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()