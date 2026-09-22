from time import sleep_ms
from collections import namedtuple
from micropython import const
from machine import Pin, I2C, reset


I2C_BUS     = const(0x01)
I2C_PIN_SDA = const(0x06)
I2C_PIN_SCL = const(0x07)
I2C_ADDRESS = const(0x1F)
I2C_FREQ    = const(100_000)

ALT         = const(0xA1)
SHL         = const(0xA2)
SHR         = const(0xA3)
SYM         = const(0xA4)
CTRL        = const(0xA5)

BACKSPACE   = const(0x08)
TAB         = const(0x09)
ENTER       = const(0x0A)
SPACE       = const(0x20)
ESC         = const(0xB1)
UP          = const(0xB5)
DOWN        = const(0xB6)
LEFT        = const(0xB4)
RIGHT       = const(0xB7)
BREAK       = const(0xD0)
INSERT      = const(0xD1)
HOME        = const(0xD2)
DEL         = const(0xD4)
END         = const(0xD5)
PAGE_UP     = const(0xD6)
PAGE_DOWN   = const(0xD7)
CAPS_LOCK   = const(0xC1)
F1          = const(0x81)
F2          = const(0x82)
F3          = const(0x83)
F4          = const(0x84)
F5          = const(0x85)
F6          = const(0x86)
F7          = const(0x87)
F8          = const(0x88)
F9          = const(0x89)
F10         = const(0x90)
POWER       = const(0x91)

class BIOS(object):

    _self = None

    REG_VER = b'\x00'
    REG_KEY = b'\x04'
    REG_BLK = b'\x05'
    REG_RST = b'\x08'
    REG_FIF = b'\x09'
    REG_BK2 = b'\x0A'
    REG_BAT = b'\x0B'
    REG_PWR = b'\x8E'

    def __new__(cls, *args, **kwargs):
        if cls._self is None:
            cls._self = super().__new__(cls)
            cls._self._initialized = False
        return cls._self

    def __init__(self):
        if self._initialized:
            return
        self._i2c = I2C(I2C_BUS, 
                        sda=Pin(I2C_PIN_SDA), 
                        scl=Pin(I2C_PIN_SCL), 
                        freq=I2C_FREQ)
        self._initialized = True

    def exchange(self, command, nbytes):
        result = None
        try:
            self._i2c.writeto(I2C_ADDRESS, command)
            result = self._i2c.readfrom(I2C_ADDRESS, nbytes)
        except OSError:
            pass
        return result


class Keyboard(object):

    BTN_PRESSED  = 1
    BTN_HOLD     = 2
    BTN_RELEASED = 3
    KEY = namedtuple('KEY', ('mode', 'code'))

    def __init__(self):
        self._bus = BIOS()
        self._alt = False
        self._sht = False
        self._ctrl = False

    def read_key(self):
        result = None
        data = self._bus.exchange(self._bus.REG_FIF, 2)
        if data and len(data) == 2:
            event, code = data
            if event == self.BTN_PRESSED:
                if code == CTRL:
                    self._ctrl = True
                elif code == ALT:
                    self._alt = True
                elif code == SHL or code == SHR:
                    self._sht = True
                elif self._ctrl and self._alt and code == DEL:
                    reset()
                elif self._ctrl and code == ord('c'):
                    raise KeyboardInterrupt
                else:
                    mode = (self._ctrl << 2) | (self._alt << 1) | (self._sht << 0)
                    result = self.KEY(mode, code)
            elif event == self.BTN_RELEASED:
                if code == CTRL:
                    self._ctrl = False
                elif code == ALT:
                    self._alt = False
                elif code == SHL or code == SHR:
                    self._sht = False
        return result

    def wait_key(self):
        while True:
            key = self.read_key()
            if key: 
                return key
            sleep_ms(50)


def read_batt():
    bios = BIOS()
    data = bios.exchange(bios.REG_BAT, 2)
    return str(int(data[1]))

def power_off(): 
    bios = BIOS()
    bios.exchange(bios.REG_PWR + b'\x00', 1)