'''
 * MAX7219 VCC pin to VBUS
 * MAX7219 GND pin to GND
 * MAX7219 DIN pin to digital GPIO3
 * MAX7219 CS pin to digital GPIO5
 * MAX7219 CLOCK pin to digital GPIO2
'''

from machine import Pin, SPI
import max7219
from utime import sleep

from constants import *

BORDER_X1 = 4
BORDER_X2 = 7
BORDER_Y1 = 12
BORDER_Y2 = 31
BORDER_Y3 = 44
BORDER_Y4 = 63

def display_coords(x, y):
    x = SCREEN_WIDTH - x - 1
    addr_y = y
    if x >= HALF_WIDTH:
        addr_y += SCREEN_HEIGHT
    return addr_y, x % HALF_WIDTH

def get_pixel(x, y):
    x, y = display_coords(x, y)
    return display.pixel(x, y)

def set_pixel(x, y, c):
    x, y = display_coords(x, y)
    display.pixel(x, y, c)

spi = SPI(0, baudrate=10000000, polarity=1, phase=0, sck=Pin(2), mosi=Pin(3))
ss = Pin(5, Pin.OUT)

display = max7219.Matrix8x8(spi, ss, 8)

display.brightness(0)
display.fill(0)
for x in [5, 7]:
    display.pixel(11, x, 1)
for x in [1, 2, 4, 6]:
    display.pixel(43, x, 1)
display.line(BORDER_Y1, BORDER_X1, BORDER_Y2, BORDER_X1, 1)
display.line(BORDER_Y3, BORDER_X2, BORDER_Y4, BORDER_X2, 1)
display.line(BORDER_Y2, BORDER_X1, BORDER_Y2, MAX_X, 1)
display.line(BORDER_Y4, 0, BORDER_Y4, BORDER_X2, 1)
display.show()

sleep(0.1)

def update_score(score):
    # TODO
    pass

def update_display():
    display.show()
    sleep(TIME_STEP)

from audio import *

try:
    asyncio.run(audio())
except KeyboardInterrupt:
    for ch in (ch1, ch2, ch3, ch4):
        ch.duty_u16(0)
        sm_noise.active(0)
        noise_pin.value(0)
        print("Stopped.")

from tetris import *
