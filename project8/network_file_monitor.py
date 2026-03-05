import os
import pickle
import hashlib
import win32wnet
import win32netcon
import win32security
import win32file
import win32con
from datetime import datetime, timedelta
from pathlib import Path
import json
from collections import defaultdict
import webbrowser
import time
import sys
from jinja2 import Template

class NetworkFileMonitor:
    """Класс для мониторинга изменений в сетевой папке СБ-Регионы"""
    
    def __init__(self, config_file='config.json'):
        # Загружаем конфигурацию
        self.config = self.load_config(config_file)
        
        # Настройки из конфига
        self.settings = self.config['settings']
        
        # Создаем папку для отчетов
        os.makedirs(self.settings['report_dir'], exist_ok=True)
        
        # Дата первой проверки
        self.first_check_date = datetime(2026, 2, 10)
        
        # Файл для хранения состояния
        self.state_file = os.path.join(self.settings['report_dir'], 'file_state.pkl')
        
        # Файл для хранения даты последней проверки
        self.last_check_file = os.path.join(self.settings['report_dir'], 'last_check.txt')
        
        # Расширения файлов для отслеживания
        self.tracked_extensions = {
            '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
            '.ppt', '.pptx', '.jpg', '.jpeg', '.png', '.csv',
            '.rtf', '.msg', '.eml', '.zip', '.rar', '.7z',
            '.xml', '.json', '.html', '.htm', '.log', '.ini',
            '.cfg', '.conf'
        }
        
        # Папки для сканирования (только корневые, без подпапок)
        self.scan_folders = [
            self.settings['source'],  # \\fs\СБ-Регионы
            os.path.join(self.settings['source'], 'Основные показатели')  # \\fs\СБ-Регионы\Основные показатели
        ]
        
        # Подключаемся к сетевой папке
        self.connect_to_network()
    
    def load_config(self, config_file):
        """Загрузка конфигурации из JSON файла"""
        default_config = {
            "settings": {
                "username": r"alkor\yakovenko",
                "password": "ЗАМЕНИТЕ_НА_ВАШ_ПАРОЛЬ",
                "source": r"\\fs\СБ-Регионы",
                "report_dir": r"D:\VSC\project8"
            }
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"✓ Конфигурация загружена из {config_file}")
                    
                    if config['settings']['password'] == "ЗАМЕНИТЕ_НА_ВАШ_ПАРОЛЬ":
                        print("⚠️  ВНИМАНИЕ: В config.json не изменен пароль!")
                    
                    return config
            else:
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=4)
                print(f"✓ Создан файл конфигурации: {config_file}")
                print(f"⚠️  Отредактируйте config.json и укажите ваш пароль!")
                return default_config
        except Exception as e:
            print(f"⚠️ Ошибка загрузки конфига: {e}")
            return default_config
    
    def log_message(self, message, level="INFO"):
        """Только вывод в консоль, без записи в файл"""
        colors = {
            "INFO": "\033[92m",
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "HEADER": "\033[95m"
        }
        reset = "\033[0m"
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if level in colors:
            print(f"{colors[level]}[{timestamp}] {message}{reset}")
        else:
            print(f"[{timestamp}] {message}")
    
    def connect_to_network(self):
        """Подключение к сетевой папке"""
        try:
            self.log_message("🔌 Подключение к сетевой папке...", "HEADER")
            
            if self.settings['password'] == "ЗАМЕНИТЕ_НА_ВАШ_ПАРОЛЬ":
                self.log_message("   ❌ Пароль не изменен в config.json!", "ERROR")
                return False
            
            net = win32wnet.NETRESOURCE()
            net.lpRemoteName = self.settings['source']
            net.dwType = win32netcon.RESOURCETYPE_DISK
            
            win32wnet.WNetAddConnection2(
                net, 
                self.settings['password'], 
                self.settings['username'], 
                0
            )
            
            self.log_message(f"   ✅ Подключение установлено от {self.settings['username']}", "INFO")
            time.sleep(1)
            return True
            
        except Exception as e:
            self.log_message(f"   ❌ Ошибка подключения: {e}", "ERROR")
            return False
    
    def disconnect_from_network(self):
        """Отключение от сетевой папки"""
        try:
            win32wnet.WNetCancelConnection2(self.settings['source'], 0, True)
            self.log_message("   🔌 Подключение закрыто", "INFO")
        except:
            pass
    
    def get_last_check_date(self):
        """Получение даты последней проверки"""
        try:
            if os.path.exists(self.last_check_file):
                with open(self.last_check_file, 'r', encoding='utf-8') as f:
                    date_str = f.read().strip()
                    return datetime.strptime(date_str, '%d.%m.%Y %H:%M:%S')
        except:
            pass
        return self.first_check_date
    
    def save_check_date(self, date):
        """Сохранение даты последней проверки"""
        try:
            with open(self.last_check_file, 'w', encoding='utf-8') as f:
                f.write(date.strftime('%d.%m.%Y %H:%M:%S'))
        except:
            pass
    
    def load_previous_state(self):
        """Загрузка предыдущего состояния"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'rb') as f:
                    return pickle.load(f)
        except:
            pass
        return {}
    
    def save_current_state(self, state):
        """Сохранение текущего состояния"""
        try:
            with open(self.state_file, 'wb') as f:
                pickle.dump(state, f)
            self.log_message(f"💾 Состояние сохранено ({len(state)} файлов)", "INFO")
        except Exception as e:
            self.log_message(f"❌ Ошибка сохранения состояния: {e}", "ERROR")
    
    def scan_folders_only(self, last_check_date):
        """Сканирование только указанных папок без подпапок"""
        
        self.log_message(f"\n🔍 Сканирование целевых папок...", "HEADER")
        self.log_message(f"   📅 Проверяем изменения с: {last_check_date.strftime('%d.%m.%Y %H:%M:%S')}", "INFO")
        
        changed_files = []
        new_files = []
        deleted_files = []
        total_scanned = 0
        
        previous_state = self.load_previous_state()
        current_state = {}
        
        try:
            for folder in self.scan_folders:
                if not os.path.exists(folder):
                    self.log_message(f"   ⚠️ Папка не существует: {folder}", "WARNING")
                    continue
                
                folder_name = os.path.basename(folder) if folder != self.settings['source'] else 'Корень'
                self.log_message(f"\n📁 Сканирование: {folder_name}", "INFO")
                
                try:
                    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
                except Exception as e:
                    self.log_message(f"   ❌ Ошибка доступа к {folder}: {e}", "ERROR")
                    continue
                
                for filename in files:
                    if filename.startswith('~$') or filename == 'Thumbs.db' or filename.endswith('.tmp'):
                        continue
                    
                    filepath = os.path.join(folder, filename)
                    total_scanned += 1
                    
                    try:
                        stat = os.stat(filepath)
                        mod_time = datetime.fromtimestamp(stat.st_mtime)
                        create_time = datetime.fromtimestamp(stat.st_ctime)
                        file_size = stat.st_size
                        
                        # Получаем владельца файла (кто создал/изменил)
                        owner = "Неизвестно"
                        try:
                            sd = win32security.GetFileSecurity(
                                filepath, 
                                win32security.OWNER_SECURITY_INFORMATION
                            )
                            owner_sid = sd.GetSecurityDescriptorOwner()
                            owner_name, domain, _ = win32security.LookupAccountSid(None, owner_sid)
                            owner = f"{domain}\\{owner_name}"
                        except:
                            pass
                        
                        _, ext = os.path.splitext(filename)
                        ext = ext.lower()
                        
                        if folder == self.settings['source']:
                            relative_path = ''
                        else:
                            relative_path = os.path.basename(folder)
                        
                        file_info = {
                            'mod_time': mod_time,
                            'create_time': create_time,
                            'size': file_size,
                            'filename': filename,
                            'extension': ext,
                            'relative_path': relative_path,
                            'full_path': filepath,
                            'owner': owner
                        }
                        
                        current_state[filepath] = file_info
                        
                        # Проверяем новый файл
                        if filepath not in previous_state:
                            if create_time > last_check_date:
                                new_files.append(file_info)
                                self.log_message(f"   ✨ Новый файл: {filename} (создан: {create_time.strftime('%d.%m.%Y %H:%M')}, владелец: {owner})", "INFO")
                            else:
                                self.log_message(f"   📎 Существующий файл: {filename} (создан: {create_time.strftime('%d.%m.%Y')})", "INFO")
                                
                                # ВАЖНО! Даже старый файл мог быть изменен после последней проверки
                                if mod_time > last_check_date:
                                    changed_files.append(file_info)
                                    self.log_message(f"   📝 ИЗМЕНЕН: {filename} (модифицирован: {mod_time.strftime('%d.%m.%Y %H:%M')}, владелец: {owner})", "INFO")
                        
                        # Существующий файл (был в предыдущем состоянии)
                        else:
                            prev_info = previous_state[filepath]
                            is_changed = False
                            
                            if mod_time > last_check_date:
                                is_changed = True
                                self.log_message(f"   📝 Изменен: {filename} (модифицирован: {mod_time.strftime('%d.%m.%Y %H:%M')}, владелец: {owner})", "INFO")
                            elif prev_info['size'] != file_size:
                                is_changed = True
                                self.log_message(f"   📝 Изменен размер: {filename} (был: {prev_info['size']}, стал: {file_size})", "INFO")
                            elif mod_time != prev_info['mod_time']:
                                is_changed = True
                                self.log_message(f"   📝 Изменена дата: {filename}", "INFO")
                            
                            if is_changed:
                                changed_files.append(file_info)
                    
                    except (PermissionError, OSError):
                        continue
                    except Exception as e:
                        continue
                
                time.sleep(0.5)
            
            # Проверяем удаленные файлы
            for filepath in previous_state:
                if filepath not in current_state:
                    if any(filepath.startswith(folder) for folder in self.scan_folders):
                        deleted_files.append(previous_state[filepath])
                        self.log_message(f"   🗑️ Удален: {previous_state[filepath]['filename']}", "WARNING")
            
        except Exception as e:
            self.log_message(f"❌ Ошибка: {e}", "ERROR")
        
        self.log_message(f"\n📊 Итоги:", "HEADER")
        self.log_message(f"   📄 Файлов проверено: {total_scanned}", "INFO")
        self.log_message(f"   ✨ Новых: {len(new_files)}", "INFO")
        self.log_message(f"   📝 Измененных: {len(changed_files)}", "INFO")
        self.log_message(f"   🗑️ Удаленных: {len(deleted_files)}", "WARNING")
        
        return current_state, new_files, changed_files, deleted_files
    
    def generate_dashboard(self, new_files, changed_files, deleted_files, check_date):
        """Генерация HTML дашборда"""
        self.log_message("\n📊 Генерация отчета...", "HEADER")
        
        new_by_folder = defaultdict(list)
        changed_by_folder = defaultdict(list)
        deleted_by_folder = defaultdict(list)
        
        for file in new_files:
            folder = file['relative_path'] if file['relative_path'] else 'Корень'
            new_by_folder[folder].append(file)
        
        for file in changed_files:
            folder = file['relative_path'] if file['relative_path'] else 'Корень'
            changed_by_folder[folder].append(file)
        
        for file in deleted_files:
            folder = file['relative_path'] if file['relative_path'] else 'Корень'
            deleted_by_folder[folder].append(file)
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Мониторинг СБ-Регионы</title>
            <style>
                body { 
                    font-family: 'Segoe UI', Arial, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }
                .container { 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 30px; 
                    border-radius: 15px; 
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                }
                h1 { 
                    color: #333; 
                    margin-bottom: 20px; 
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                .date-info {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 25px;
                    color: #666;
                }
                .stats { 
                    display: grid; 
                    grid-template-columns: repeat(3,1fr); 
                    gap: 20px; 
                    margin: 25px 0; 
                }
                .stat-card { 
                    padding: 25px; 
                    border-radius: 12px; 
                    color: white; 
                    text-align: center;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                }
                .new { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
                .changed { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
                .deleted { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }
                .stat-number { font-size: 42px; font-weight: bold; margin-bottom: 5px; }
                .stat-label { font-size: 16px; opacity: 0.9; }
                .section { 
                    margin: 30px 0; 
                    border: 1px solid #e0e0e0; 
                    border-radius: 12px; 
                    overflow: hidden;
                }
                .section-header { 
                    background: #f8f9fa; 
                    padding: 15px 20px; 
                    border-bottom: 1px solid #e0e0e0;
                    font-size: 18px;
                    font-weight: 600;
                }
                .folder { 
                    margin: 15px; 
                    padding: 15px; 
                    background: #f8f9fa; 
                    border-radius: 8px; 
                    border-left: 4px solid #667eea;
                }
                .folder-name { 
                    font-weight: 600; 
                    margin-bottom: 15px; 
                    color: #495057;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .file-item { 
                    padding: 12px; 
                    border-bottom: 1px solid #e0e0e0; 
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                .file-item:last-child { border-bottom: none; }
                .file-name { font-weight: 500; color: #333; }
                .file-meta { font-size: 12px; color: #6c757d; margin-left: 10px; }
                .owner { 
                    font-size: 11px; 
                    color: #4a6fa5; 
                    background: #e7f1ff; 
                    padding: 2px 6px; 
                    border-radius: 12px;
                    display: inline-block;
                    margin-left: 5px;
                }
                .empty-state { 
                    text-align: center; 
                    padding: 40px; 
                    color: #6c757d; 
                    font-style: italic;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>
                    <span style="font-size: 32px;">📋</span>
                    Мониторинг изменений в папке СБ-Регионы
                </h1>
                
                <div class="date-info">
                    <strong>📅 Проверка с:</strong> {{ check_date }} &nbsp;&nbsp; 
                    <strong>🕐 Отчет создан:</strong> {{ current_time }}
                </div>
                
                <div class="stats">
                    <div class="stat-card new">
                        <div class="stat-number">{{ new_count }}</div>
                        <div class="stat-label">✨ Новых файлов</div>
                    </div>
                    <div class="stat-card changed">
                        <div class="stat-number">{{ changed_count }}</div>
                        <div class="stat-label">📝 Измененных</div>
                    </div>
                    <div class="stat-card deleted">
                        <div class="stat-number">{{ deleted_count }}</div>
                        <div class="stat-label">🗑️ Удаленных</div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-header">✨ Новые файлы</div>
                    <div class="section-content">
                        {% if new_files %}
                            {% for folder, files in new_by_folder.items() %}
                            <div class="folder">
                                <div class="folder-name">📁 {{ folder }}</div>
                                {% for file in files %}
                                <div class="file-item">
                                    <span>📄</span>
                                    <span class="file-name">{{ file.filename }}</span>
                                    <span class="file-meta">
                                        {{ (file.size/1024)|round(1) }} KB, 
                                        создан: {{ file.create_time.strftime('%d.%m.%Y %H:%M') }}
                                    </span>
                                    <span class="owner">👤 {{ file.owner }}</span>
                                </div>
                                {% endfor %}
                            </div>
                            {% endfor %}
                        {% else %}
                            <div class="empty-state">✨ Новых файлов нет</div>
                        {% endif %}
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-header">📝 Измененные файлы</div>
                    <div class="section-content">
                        {% if changed_files %}
                            {% for folder, files in changed_by_folder.items() %}
                            <div class="folder">
                                <div class="folder-name">📁 {{ folder }}</div>
                                {% for file in files %}
                                <div class="file-item">
                                    <span>📝</span>
                                    <span class="file-name">{{ file.filename }}</span>
                                    <span class="file-meta">
                                        {{ (file.size/1024)|round(1) }} KB, 
                                        изменен: {{ file.mod_time.strftime('%d.%m.%Y %H:%M') }}
                                    </span>
                                    <span class="owner">👤 {{ file.owner }}</span>
                                </div>
                                {% endfor %}
                            </div>
                            {% endfor %}
                        {% else %}
                            <div class="empty-state">📝 Измененных файлов нет</div>
                        {% endif %}
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-header">🗑️ Удаленные файлы</div>
                    <div class="section-content">
                        {% if deleted_files %}
                            {% for folder, files in deleted_by_folder.items() %}
                            <div class="folder">
                                <div class="folder-name">📁 {{ folder }}</div>
                                {% for file in files %}
                                <div class="file-item">
                                    <span>🗑️</span>
                                    <span class="file-name">{{ file.filename }}</span>
                                    <span class="file-meta">
                                        удален, был изменен: {{ file.mod_time.strftime('%d.%m.%Y %H:%M') }}
                                    </span>
                                    <span class="owner">👤 {{ file.owner }}</span>
                                </div>
                                {% endfor %}
                            </div>
                            {% endfor %}
                        {% else %}
                            <div class="empty-state">🗑️ Удаленных файлов нет</div>
                        {% endif %}
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #6c757d; font-size: 12px;">
                    📊 Отчет сгенерирован автоматически системой мониторинга СБ-Регионы
                </div>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(
            check_date=check_date.strftime('%d.%m.%Y %H:%M'),
            current_time=datetime.now().strftime('%d.%m.%Y %H:%M'),
            new_count=len(new_files),
            changed_count=len(changed_files),
            deleted_count=len(deleted_files),
            new_by_folder=new_by_folder,
            changed_by_folder=changed_by_folder,
            deleted_by_folder=deleted_by_folder,
            new_files=new_files,
            changed_files=changed_files,
            deleted_files=deleted_files
        )
        
        report_filename = f"monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        report_path = os.path.join(self.settings['report_dir'], report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        latest_path = os.path.join(self.settings['report_dir'], 'latest_monitoring.html')
        with open(latest_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.log_message(f"   ✅ Отчет сохранен: {report_filename}", "INFO")
        
        return latest_path
    
    def run_monitoring(self):
        """Основная функция мониторинга"""
        try:
            self.log_message("=" * 60, "HEADER")
            self.log_message(f"🚀 ЗАПУСК МОНИТОРИНГА: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", "HEADER")
            self.log_message("=" * 60, "HEADER")
            
            last_check_date = self.get_last_check_date()
            
            if self.settings['password'] == "ЗАМЕНИТЕ_НА_ВАШ_ПАРОЛЬ":
                self.log_message("❌ ОШИБКА: Пароль не указан в config.json!", "ERROR")
                self.log_message("   Отредактируйте файл config.json и укажите ваш пароль", "WARNING")
                return
            
            current_state, new_files, changed_files, deleted_files = self.scan_folders_only(last_check_date)
            
            self.save_current_state(current_state)
            self.save_check_date(datetime.now())
            
            if new_files or changed_files or deleted_files:
                report_path = self.generate_dashboard(new_files, changed_files, deleted_files, last_check_date)
                webbrowser.open('file://' + os.path.abspath(report_path))
                self.log_message("\n✅ Мониторинг завершен!", "HEADER")
            else:
                self.log_message("\n📭 Изменений не обнаружено", "INFO")
            
        except Exception as e:
            self.log_message(f"❌ Ошибка: {e}", "ERROR")
            import traceback
            traceback.print_exc()
        finally:
            self.disconnect_from_network()

def main():
    """Главная функция"""
    print("=" * 60)
    print("📋 МОНИТОРИНГ СБ-РЕГИОНЫ (с информацией о владельце)")
    print("=" * 60)
    print("   ✅ Только корневые папки (2 папки)")
    print("   ✅ Без вложенных папок")
    print("   ✅ Без логирования в файлы")
    print("   ✅ Пароль в отдельном JSON")
    print("   ✅ Отображается владелец файла")
    print("=" * 60)
    
    monitor = NetworkFileMonitor()
    monitor.run_monitoring()
    return 0

if __name__ == "__main__":
    sys.exit(main())