import pyautogui
import time

print(
    "Move o mouse para o elemento desejado. O programa vai capturar as coordenadas em 5 segundos..."
)
time.sleep(5)

x, y = pyautogui.position()
print(f"Coordenadas do mouse: {x}, {y}")
