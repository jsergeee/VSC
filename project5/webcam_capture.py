import cv2
import os
import threading
import time

# НАСТРОЙКИ
PHOTOS = 30          # Сколько фото
INTERVAL = 2         # Секунд
FOLDER = "fast_cams"

def capture_camera(cam_id, total_photos, folder):
    """Функция для захвата с одной камеры"""
    cam_folder = f"{folder}/cam_{cam_id}"
    os.makedirs(cam_folder, exist_ok=True)
    
    print(f"📷 Камера #{cam_id} запущена")
    
    for i in range(total_photos):
        cap = cv2.VideoCapture(cam_id, cv2.CAP_DSHOW)
        ret, frame = cap.read()
        
        if ret:
            filename = f"{cam_folder}/photo_{i+1:03d}.jpg"
            cv2.imwrite(filename, frame)
        
        cap.release()
        
        if i < total_photos - 1:
            time.sleep(INTERVAL)
    
    print(f"✅ Камера #{cam_id} завершила ({total_photos} фото)")

# Основной код
print("⚡ БЫСТРЫЙ ПАРАЛЛЕЛЬНЫЙ ЗАХВАТ")
print("="*40)

# Находим камеры
cameras = []
for i in range(4):
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    if cap.read()[0]:
        cameras.append(i)
        print(f"Камера #{i} - OK")
    cap.release()

if not cameras:
    print("Нет камер!")
    exit()

print(f"\nНайдено: {len(cameras)} камер")
print(f"Буду делать: {PHOTOS} фото с каждой")
print(f"Интервал: {INTERVAL} сек.")
print(f"Папка: {FOLDER}")

os.makedirs(FOLDER, exist_ok=True)

# Запускаем потоки для каждой камеры
threads = []
for cam in cameras:
    t = threading.Thread(target=capture_camera, args=(cam, PHOTOS, FOLDER))
    t.start()
    threads.append(t)

# Ждем завершения всех потоков
for t in threads:
    t.join()

print(f"\n🎉 ВСЕ КАМЕРЫ ЗАВЕРШИЛИ РАБОТУ!")
print(f"📁 Проверьте папку: {os.path.abspath(FOLDER)}")