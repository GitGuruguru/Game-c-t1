"""Small Windows console fallback for the subset of curses used by Starfall."""
import os
import shutil
import sys

if os.name != "nt":  # The real curses module is available on Unix-like systems.
    raise ImportError("curses_compat is only for Windows")

import msvcrt

try:
    import ctypes
    _stdout = ctypes.windll.kernel32.GetStdHandle(-11)
    _mode = ctypes.c_uint()
    if ctypes.windll.kernel32.GetConsoleMode(_stdout, ctypes.byref(_mode)):
        ctypes.windll.kernel32.SetConsoleMode(_stdout, _mode.value | 0x0004)
except (AttributeError, OSError):
    pass

error = OSError
KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT = 259, 258, 260, 261
A_BOLD, A_DIM, A_BLINK = 1, 2, 4
COLOR_BLACK, COLOR_RED, COLOR_GREEN, COLOR_YELLOW = 0, 1, 2, 3
COLOR_BLUE, COLOR_MAGENTA, COLOR_CYAN, COLOR_WHITE = 4, 5, 6, 7
ALL_MOUSE_EVENTS = REPORT_MOUSE_POSITION = 0
BUTTON1_CLICKED = 0
_color_by_pair = {}


def has_colors():
    return True


def start_color():
    return None


def use_default_colors():
    return None


def init_pair(pair, foreground, background=-1):
    _color_by_pair[pair] = foreground


def color_pair(pair):
    return pair << 8


def curs_set(_visibility):
    return 0


def mousemask(_mask):
    return 0


def getmouse():
    raise error("Mouse input is not available in the Windows console fallback")


def _ansi_color(foreground):
    return (30, 31, 32, 33, 34, 35, 36, 37)[foreground % 8]


class _Screen:
    def __init__(self):
        self._keypad = False
        self._nodelay = False
        self._buffer = []
        self._last_size = (0, 0)

    def getmaxyx(self):
        size = shutil.get_terminal_size((80, 24))
        return size.lines, size.columns

    def keypad(self, enabled):
        self._keypad = enabled

    def nodelay(self, enabled):
        self._nodelay = enabled

    def timeout(self, milliseconds):
        self._nodelay = milliseconds == 0

    def erase(self):
        self._buffer = []

    clear = erase

    def border(self):
        rows, cols = self.getmaxyx()
        if rows < 2 or cols < 2:
            return
        self.addstr(0, 0, "+" + "-" * (cols - 2) + "+")
        self.addstr(rows - 1, 0, "+" + "-" * (cols - 2) + "+")
        for y in range(1, rows - 1):
            self.addstr(y, 0, "|")
            self.addstr(y, cols - 1, "|")

    def addstr(self, y, x, value, attr=0):
        self._buffer.append((y, x, str(value), attr))

    def addch(self, y, x, value, attr=0):
        self.addstr(y, x, value, attr)

    def refresh(self):
        rows, cols = self.getmaxyx()
        frame = ["\x1b[2J\x1b[H"]
        for y, x, value, attr in self._buffer:
            if not (0 <= y < rows and 0 <= x < cols):
                continue
            pair = (attr >> 8) & 0xFF
            codes = []
            if attr & A_BOLD:
                codes.append("1")
            elif attr & A_DIM:
                codes.append("2")
            elif attr & A_BLINK:
                codes.append("5")
            if pair in _color_by_pair:
                codes.append(str(_ansi_color(_color_by_pair[pair])))
            prefix = "\x1b[" + ";".join(codes) + "m" if codes else ""
            visible = value[:max(0, cols - x)]
            frame.append(f"\x1b[{y + 1};{x + 1}H{prefix}{visible}\x1b[0m")
        frame.append(f"\x1b[{rows};1H")
        sys.stdout.write("".join(frame))
        sys.stdout.flush()
        self._buffer = []

    def getch(self):
        if not msvcrt.kbhit():
            return -1
        char = msvcrt.getwch()
        if char in ("\x00", "\xe0"):
            ext = msvcrt.getwch()
            return {"H": KEY_UP, "P": KEY_DOWN, "K": KEY_LEFT, "M": KEY_RIGHT}.get(ext, -1)
        if char == "\r":
            return 10
        return ord(char)


def wrapper(function):
    screen = _Screen()
    sys.stdout.write("\x1b[?1049h\x1b[?25l")
    try:
        function(screen)
    finally:
        sys.stdout.write("\x1b[0m\x1b[?25h\x1b[?1049l\n")
        sys.stdout.flush()
