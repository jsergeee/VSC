from mss import mss
from PIL import Image

with mss() as sct:
    # Скриншот всего экрана
    screenshot = sct.shot(output='screenshot.png')
    
    # Скриншот определенного монитора
    monitor = sct.monitors[1]  # второй монитор
    screenshot = sct.grab(monitor)
    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    img.save('screenshot.png')