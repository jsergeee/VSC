#!/usr/bin/env python3
import subprocess
import sys

def test_simple():
    """Простой тест nmap"""
    print("Тест nmap...")
    
    # Проверка nmap
    try:
        result = subprocess.run(['nmap', '--version'], 
                               capture_output=True, 
                               timeout=10)
        print(f"Nmap найден, код: {result.returncode}")
        return True
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

if __name__ == "__main__":
    if test_simple():
        print("Тест пройден успешно!")
        sys.exit(0)
    else:
        print("Тест не пройден!")
        sys.exit(1)