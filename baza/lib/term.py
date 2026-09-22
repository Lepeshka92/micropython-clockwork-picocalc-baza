from micropython import const
from framebuf import FrameBuffer, RGB565 
from bios import SPACE, LEFT, RIGHT, BACKSPACE, DEL, ENTER, ESC


BLACK   = const(0x0000)
RED     = const(0x00F8)
GREEN   = const(0xE007)
YELLOW  = const(0xE0FF)
BLUE    = const(0x1F00)
MAGENTA = const(0x1FF8)
CYAN    = const(0xFF07)
WHITE   = const(0xFFFF)
PALETTE = (BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE)


class Terminal(object):

    _self = None

    def __new__(cls, *args, **kwargs):
        if cls._self is None:
            cls._self = super().__new__(cls)
            cls._self._initialized = False
        return cls._self

    def __init__(self, display, keyboard=None, cols=40, rows=25):
        if self._initialized:
            return

        self._scr = display
        self._kbd = keyboard

        self._cols = cols
        self._rows = rows
        self._col = 0 
        self._row = 0
        self._top = 0
        self._tb = bytearray(self._cols * self._rows) 
        self._mv = memoryview(self._tb)

        self._bg = BLACK
        self._fg = WHITE
        self._fw = self._scr.w // self._cols
        self._fh = self._scr.h // self._rows
        self._ba = bytearray(self._fw * self._fh * 2)
        self._fb = FrameBuffer(self._ba, self._fw, self._fh, RGB565)
        self._initialized = True

    def _pos(self, col, row):
        return ((self._top + row) % self._rows) * self._cols + col

    def _draw_char(self, col, row, code):
        x = col * self._fw
        y = row * self._fh

        if code in (ENTER, 0x0A):
            code = SPACE

        self._fb.fill(self._bg)
        self._fb.text(chr(code), 0, 0, self._fg)
        self._scr.blit(x, y, self._fw, self._fh, self._fb)

    def _draw_curs(self, col, row, show=True):
        x = col * self._fw
        y = row * self._fh + self._fh - 1
        color = self._fg if show else self._bg
        self._scr.hline(x, y, self._fw, color)

    def get_color(self):
        return self._bg, self._fg

    def set_color(self, bg=None, fg=None):
        if bg:
            self._bg = bg
        if fg:
            self._fg = fg

    def is_printable(self, code):
        return 32 <= code <= 126 or code in (ENTER, 0x0A)

    def clear_screen(self):
        for i in range(len(self._tb)):
            self._mv[i] = SPACE
        self._col = 0
        self._row = 0
        self._top = 0
        self._scr.fill(self._bg)

    def scroll(self):
        sp = self._pos(0, self._rows)
        for i in range(sp, sp + self._cols):
            self._mv[i] = SPACE
        self._top = (self._top + 1) % self._rows
        if self._row > 0:
            self._row -= 1
            self._scr.scroll(self._fh, self._bg)

    def write_char(self, code):
        self._draw_char(self._col, self._row, code)
        self._mv[self._pos(self._col, self._row)] = code
        self._col += 1
        if self._col >= self._cols or code == ENTER:
            self._col = 0
            self._row += 1
        if self._row >= self._rows:
            self.scroll()

    def write(self, text, bg=None, fg=None):
        if bg or fg:
            _bg, _fg = self.get_color()
            self.set_color(bg, fg)
        for c in text:
            code = ord(c) if isinstance(c, str) else c
            if not self.is_printable(code):
                code = 0x3A
            self.write_char(code)
        if bg or fg:
            self.set_color(_bg, _fg)

    def writeline(self, text, bg=None, fg=None):
        self.write(text + chr(ENTER), bg, fg)

    def read_key(self, wait=False):
        result = None
        if self._kbd:
            result = self._kbd.wait_key() if wait else self._kbd.read_key()
        return result

    def readline(self, ps=None):
        if not self._kbd:
            return ''
        if ps:
            self.write(ps)

        col, row, top = self._col, self._row, self._top
        cur_col, cur_row = self._col, self._row
        pos = 0
        upd = False
        line = []
        self._draw_curs(cur_col, cur_row, True)
        while True:
            key = self._kbd.wait_key()

            self._draw_curs(cur_col, cur_row, False)
            if key.code == ENTER:
                break
            elif key.code == ESC:
                line.clear()
                break
            elif key.code == LEFT and pos > 0:
                pos -= 1
                upd = False
            elif key.code == RIGHT and pos < len(line):
                pos += 1
                upd = False
            elif self.is_printable(key.code):
                line.insert(pos, chr(key.code))
                pos += 1
                upd = True
            elif key.code == BACKSPACE and pos > 0:
                pos -= 1
                line.pop(pos)
                upd = True
            elif key.code == DEL and pos < len(line):
                line.pop(pos)
                upd = True
            if upd:
                self._col = col
                self._row = row - (self._top - top)
                self.write(''.join(line))
                self.write_char(SPACE)

            r, cur_col = divmod(col + pos, self._cols)
            cur_row = row + r - (self._top - top)
            self._draw_curs(cur_col, cur_row, True)

        self.write_char(ENTER)
        return ''.join(line).strip()