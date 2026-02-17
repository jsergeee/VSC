#!/usr/bin/env python3
# Тестовый запуск сканера

import subprocess
import sys

def decode_output(bytes_output):
    """Декодирование вывода с учетом русской кодировки"""
    try:
        return bytes_output.decode('utf-8')
    except UnicodeDecodeError:
        try:
            return bytes_output.decode('cp866')
        except UnicodeDecodeError:
            return bytes_output.decode('latin-1', errors='replace')

def test_scanner():
    """Тестовый запуск сканера сети"""
    print("Тестовый запуск сканера сети...")
    
    try:
        # Запускаем сканер с ограниченным временем
        result = subprocess.run(
            [sys.executable, "scan-net.py"],
            capture_output=True,
            timeout=300  # 5 минут
        )
        
        # Декодируем вывод
        stdout = decode_output(result.stdout)
        stderr = decode_output(result.stderr)
        
        print(f"Код возврата: {result.returncode}")
        print("\nВывод сканера:")
        print("-" * 60)
        print(stdout[:2000])  # Первые 2000 символов
        
        if stderr:
            print("\nОшибки:")
            print("-" * 60)
            print(stderr[:1000])
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("Сканирование превысило время ожидания")
        return False
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_scanner()
    sys.exit(0 if success else 1)