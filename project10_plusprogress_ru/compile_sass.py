import os
import sys

try:
    import sass

    print("✅ libsass найден, компилируем...")

    # Пути к файлам
    scss_path = os.path.join('static', 'scss', 'main.scss')
    css_path = os.path.join('static', 'css', 'main.css')

    # Проверяем существование SCSS файла
    if not os.path.exists(scss_path):
        print(f"❌ Файл {scss_path} не найден!")
        # Показываем что есть в папке
        if os.path.exists('static/scss'):
            print("Файлы в static/scss:")
            for f in os.listdir('static/scss'):
                print(f"  - {f}")
        sys.exit(1)

    print(f"📁 Читаем: {scss_path}")

    # Читаем SCSS
    with open(scss_path, 'r', encoding='utf-8') as f:
        scss_content = f.read()

    print(f"📏 Размер SCSS: {len(scss_content)} байт")

    # Компилируем
    print("🔄 Компиляция...")
    css_content = sass.compile(string=scss_content, output_style='expanded')

    # Создаем папку css если её нет
    os.makedirs(os.path.join('static', 'css'), exist_ok=True)

    # Записываем CSS
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_content)

    print(f"✅ Готово! CSS сохранен в: {css_path}")
    print(f"📏 Размер CSS: {len(css_content)} байт")

    # Проверяем что файл создан
    if os.path.exists(css_path):
        print("✅ Файл успешно создан!")
    else:
        print("❌ Файл не создан!")

except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
except Exception as e:
    print(f"❌ Ошибка: {e}")