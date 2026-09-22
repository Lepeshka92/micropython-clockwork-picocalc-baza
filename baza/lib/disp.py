from time import sleep_ms
from struct import pack
from micropython import const
from machine import Pin, SPI


SPI_BUS      = const(1)
SPI_SPEED    = const(75_000_000)

SPI_PIN_CS   = const(13)
SPI_PIN_DC   = const(14)
SPI_PIN_RST  = const(15)
SPI_PIN_SCK  = const(10)
SPI_PIN_MOSI = const(11)
SPI_PIN_MISO = const(12)


def swap_color(color):
    return ((color & 0xFF) << 8) | (color >> 8)


class Display(object):

    SWRESET  = b'\x01'
    SLPIN    = b'\x10'
    SLPOUT   = b'\x11'
    PTLON    = b'\x12'
    NORON    = b'\x13'
    INVOFF   = b'\x20'
    INVON    = b'\x21'
    DISPOFF  = b'\x28'
    DISPON   = b'\x29'
    CASET    = b'\x2A'
    RASET    = b'\x2B'
    RAMWR    = b'\x2C'
    RAMRD    = b'\x2E'
    PTLAR    = b'\x30'
    VSCRDEF  = b'\x33'
    MADCTL   = b'\x36'
    VSCSAD   = b'\x37'
    IDMOFF   = b'\x38'
    IDMON    = b'\x39'
    COLMOD   = b'\x3A'

    WIDTH    = 320
    HEIGHT   = 320
    VRAM_H   = 480

    def __init__(self):
        self.w   = self.WIDTH
        self.h   = self.HEIGHT
        self._h  = self.VRAM_H
        self._sp = 0

        self._cs  = Pin(SPI_PIN_CS, Pin.OUT, value=1)
        self._dc  = Pin(SPI_PIN_DC, Pin.OUT)
        self._rst = Pin(SPI_PIN_RST, Pin.OUT)
        self._spi = SPI(SPI_BUS,
                        sck=Pin(SPI_PIN_SCK, Pin.OUT),
                        mosi=Pin(SPI_PIN_MOSI, Pin.OUT),
                        miso=Pin(SPI_PIN_MISO, Pin.IN),
                        baudrate=SPI_SPEED)
        self.init()
        self.fill()

    def _set(self, cmd, buf=None):
        self._dc.value(0)
        self._cs.value(0)
        self._spi.write(cmd)
        if buf is not None:
            self._dc.value(1)
            self._spi.write(buf)
        self._cs.value(1)

    def _wnd(self, x1, y1, x2, y2):
        self._set(self.CASET, pack('>HH', x1, x2))
        self._set(self.RASET, pack('>HH', y1, y2))

    def _beg(self):
        self._dc.value(0)
        self._cs.value(0)
        self._spi.write(self.RAMWR)
        self._dc.value(1)

    def _end(self):
        self._cs.value(1)

    def _seg(self, y, h, max_y):
        y %= max_y
        if y + h <= max_y:
            return ((y, y + h),)
        return ((y, max_y), (0, y + h - max_y))

    def hw_reset(self):
        self._rst.value(0)
        sleep_ms(10)
        self._rst.value(1)
        sleep_ms(120)

    def sw_reset(self):
        self._set(self.SWRESET)
        sleep_ms(120)

    def init(self):
        self.hw_reset()
        self.sw_reset()
        self._sp = 0

        self._set(self.SLPOUT)
        self._set(self.COLMOD, b'\x55')
        self._set(self.MADCTL, b'\x48')
        self._set(self.NORON)
        self._set(self.DISPON)
        self._set(self.INVON)
        self._set(self.VSCRDEF, pack('>HHH', 0, self._h, 0))
        self._set(self.VSCSAD, pack('>H', self._sp))

    def scroll(self, n, bg=0x0000):
        if n > 0:
            self.rect(0, self.h, self.w, n, bg)
        self._sp = (self._sp + n) % self._h
        self._set(self.VSCSAD, pack('>H', self._sp))

    def rect(self, x, y, w, h, bg=0x0000):
        if x < 0 or x + w > self.w or w <= 0 or h <= 0:
            return
        y += self._sp
        chunk = pack('>H', swap_color(bg)) * w
        for y1, y2 in self._seg(y, h, self._h):
            self._wnd(x, y1, x + w - 1, y2 - 1)
            self._beg()
            for _ in range(y2 - y1):
                self._spi.write(chunk)
            self._end()

    def blit(self, x, y, w, h, buf):
        if x < 0 or x + w > self.w or w <= 0 or h <= 0:
            return
        pos, rw = 0, w * 2
        y += self._sp
        raw = memoryview(buf)
        for y1, y2 in self._seg(y, h, self._h):
            self._wnd(x, y1, x + w - 1, y2 - 1)
            self._beg()
            for _ in range(y2 - y1): 
                self._spi.write(raw[pos: pos + rw])
                pos += rw
            self._end()

    def fill(self, bg=0x0000):
        self.rect(0, 0, self.w, self._h, bg)

    def hline(self, x, y, w, fg=0xffff):
        self.rect(x, y, w, 1, fg)

    def vline(self, x, y, h, fg=0xffff):
        self.rect(x, y, 1, h, fg)