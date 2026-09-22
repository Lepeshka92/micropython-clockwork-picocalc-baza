import os
from micropython import const
from machine import Pin, SoftSPI


SPI_SPEED    = const(50_000_000)
SPI_PIN_SCK  = const(21)
SPI_PIN_CS   = const(20)
SPI_PIN_MOSI = const(2)
SPI_PIN_MISO = const(3)
SPI_PIN_IO2  = const(4)
SPI_PIN_IO3  = const(5)


class PSRAM(object):

    _self = None

    CMD_R = b'\x03'
    CMD_W = b'\x02'
    SIZE = 0x7fffff
    BLOCK_SIZE = 512

    def __new__(cls, *args, **kwargs):
        if cls._self is None:
            cls._self = super().__new__(cls)
            cls._self._initialized = False
        return cls._self

    def __init__(self):
        if self._initialized:
            return

        self._cs  = Pin(SPI_PIN_CS, Pin.OUT, value=1)
        self._spi = SoftSPI(baudrate=SPI_SPEED,
                            sck=Pin(SPI_PIN_SCK),
                            mosi=Pin(SPI_PIN_MOSI),
                            miso=Pin(SPI_PIN_MISO))
        self._addr = bytearray(3)
        self._reset()
        self._mount_point = None
        self._initialized = True

    def _reset(self):
        self._cs.value(1)
        sleep_us(200)
        self._cs.value(0)
        self._spi.write(b'\x66')
        self._cs.value(1)
        sleep_us(50)
        self._cs.value(0)
        self._spi.write(b'\x99')
        self._cs.value(1)
        sleep_us(100)

    def _read_buf(self, addr, buf):
        self._addr[0] = (addr >> 16) & 0xFF
        self._addr[1] = (addr >> 8) & 0xFF
        self._addr[2] = addr & 0xFF
        self._cs.value(0)
        self._spi.write(self.CMD_R + self._addr)
        self._spi.readinto(buf)
        self._cs.value(1)

    def _write_buf(self, addr, buf):
        self._addr[0] = (addr >> 16) & 0xFF
        self._addr[1] = (addr >> 8) & 0xFF
        self._addr[2] = addr & 0xFF
        self._cs.value(0)
        self._spi.write(self.CMD_W + self._addr)
        self._spi.write(buf)
        self._cs.value(1)

    def readblocks(self, block_num, buf, offset=0):
        addr = (block_num * self.BLOCK_SIZE) + offset
        self._read_buf(addr, buf)

    def writeblocks(self, block_num, buf, offset=0):
        addr = (block_num * self.BLOCK_SIZE) + offset
        self._write_buf(addr, buf)

    def ioctl(self, op, arg):
        if op == 1: return 0
        if op == 2: return 0
        if op == 3: return 0
        if op == 4: return (self.SIZE + 1) // self.BLOCK_SIZE
        if op == 5: return self.BLOCK_SIZE
        if op == 6: return 0
        return -1

    def mount(self, mount_point='/psram'):
        if self._mount_point is None:
            vfs = os.VfsFat(self)
            try:
                os.mount(vfs, mount_point)
            except OSError:
                os.VfsFat.mkfs(self)
                vfs = os.VfsFat(self)
                os.mount(vfs, mount_point)
            self._mount_point = mount_point

    def __len__(self):
        return self.SIZE

    def __getitem__(self, ind):
        result = None
        if isinstance(ind, int):
            if ind < 0:
                ind += self.SIZE
            if not (0 <= ind < self.SIZE):
                raise IndexError()
            data = bytearray(1)
            self._read_buf(ind, data)
            result = data[0]
        elif isinstance(ind, slice):
            start, stop, step = ind.indices(self.SIZE)
            if step != 1:
                raise NotImplementedError()
            n = max(0, stop - start)
            if n == 0:
                result = bytearray()
            else:
                data = bytearray(n)
                self._read_buf(start, data)
                result = data
        else:
            raise TypeError()
        return result

    def __setitem__(self, ind, val):
        if isinstance(ind, int):
            if ind < 0:
                ind += self.SIZE
            if not (0 <= ind < self.SIZE):
                raise IndexError()
            self._write_buf(ind, bytes([val]))
        elif isinstance(ind, slice):
            start, stop, step = ind.indices(self.SIZE)
            if step != 1:
                raise NotImplementedError()
            n = max(0, stop - start)
            data = bytes(val)
            if len(data) != n:
                raise ValueError()
            if n > 0:
                self._write_buf(start, data)
        else:
            raise TypeError()