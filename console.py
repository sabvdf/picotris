from constants import *
from time import sleep
from pynput import keyboard

from audio_stub import *

pixels = [[0 for _ in range(SCREEN_WIDTH)] for _ in range(SCREEN_HEIGHT)]

def get_pixel(x, y):
    return pixels[y][x]

def set_pixel(x, y, c):
    pixels[y][x] = c

print(chr(27) + "[2J", end="")
print(chr(27) + "[?25l", end="")
print(chr(27) + "[1;1HPicoTRIS")

for x in range(FIELD_X - 1, FIELD_X + FIELD_WIDTH + 1):
    set_pixel(x, FIELD_Y - 1, 1)
    set_pixel(x, FIELD_Y + FIELD_HEIGHT, 1)
for y in range(FIELD_Y - 1, FIELD_Y + FIELD_HEIGHT):
    set_pixel(FIELD_X - 1, y, 1)
    set_pixel(FIELD_X + FIELD_WIDTH, y, 1)

sleep(0.1)

from queue import Queue, Empty

press_queue = Queue()
release_queue = Queue()

KEY_MAP = {
    keyboard.Key.left: Inputs.LEFT,
    keyboard.Key.right: Inputs.RIGHT,
    keyboard.Key.up: Inputs.ROTATE_R,
    keyboard.Key.down: Inputs.DROP,
    keyboard.Key.space: Inputs.DROP,
    "z": Inputs.ROTATE_L,
    "x": Inputs.ROTATE_R,
    "p": Inputs.PAUSE,
    keyboard.Key.esc: Inputs.EXIT,
    "q": Inputs.EXIT
}

def on_press(key):
    if key in KEY_MAP:
        press_queue.put(KEY_MAP[key])
    if hasattr(key, "char") and key.char in KEY_MAP:
        press_queue.put(KEY_MAP[key.char])

def get_press():
    try:
        return press_queue.get_nowait()
    except Empty:
        return Inputs.NONE

def on_release(key):
    if key in KEY_MAP:
        release_queue.put(KEY_MAP[key])
    if hasattr(key, "char") and key.char in KEY_MAP:
        release_queue.put(KEY_MAP[key.char])

def get_release():
    try:
        return release_queue.get_nowait()
    except Empty:
        return Inputs.NONE

listener = keyboard.Listener(on_press=on_press, on_release=on_release, suppress=True)
listener.start()

def update_level(level):
    print(chr(27) + "[3;1H", end="")
    print(f"Level: {level}\n")
def update_score(score):
    print(chr(27) + "[3;13H", end="")
    print(f"Score: {score}\n")
def update_paused(paused):
    print(chr(27) + "[5;5H", end="")
    print(" PAUSED " if paused else "########", end="")

def update_display():
    print(chr(27) + "[5;1H", end="")

    for y in range(SCREEN_HEIGHT):
        for x in range(SCREEN_WIDTH):
            print("#" if pixels[y][x] else "·", end="")
        print("")

    sleep(TIME_STEP)

def abort():
    listener.stop()
    print(chr(27) + "[?25h\n\n")
    exit()
