# config.py
import os
from datetime import datetime, timedelta

API_ID = 25177467
API_HASH = 'd28f79d0afd5a6c3ed5d3efd3f61e56f'
SECRET_KEY = 'ye-key-delkha-mituni-chizi-benvisi'
BOT_TOKEN = '8664560534:AAE_5vo1Zx2zIDMY2DanIsj9mRv9svtZrSg'
WEB_URL = 'http://localhost:5000'
UPDATE_INTERVAL = 30

INLINE_BOT_TOKEN = '8641175379:AAHRk_y_K3X6BuhBz_ScvZxIG2a0rFe4zac'
INLINE_USERNAME = 'helperproselfbot'

SESSIONS_DIR = './sessions'
BOT_USERNAME = 'helperproselfbot'

# ========================================
# 🕐 توابع زمان تهران (UTC + 3:30)
# ========================================
def get_tehran_time(format_str="%Y-%m-%d %H:%M:%S"):
    """گرفتن زمان فعلی به افق تهران به صورت رشته"""
    utc_now = datetime.utcnow()
    tehran_offset = timedelta(hours=3, minutes=30)
    return (utc_now + tehran_offset).strftime(format_str)

def get_tehran_datetime():
    """گرفتن datetime object تهران"""
    utc_now = datetime.utcnow()
    tehran_offset = timedelta(hours=3, minutes=30)
    return utc_now + tehran_offset

# ========================================
# توابع فونت (Unicode واقعی)
# ========================================
def _convert(text, letter_lower, letter_upper=None, digit=None, colon=None):
    result = []
    for c in text:
        if 'a' <= c <= 'z' and letter_lower:
            result.append(chr(letter_lower + ord(c) - ord('a')))
        elif 'A' <= c <= 'Z' and letter_upper:
            result.append(chr(letter_upper + ord(c) - ord('A')))
        elif '0' <= c <= '9' and digit:
            result.append(chr(digit + ord(c) - ord('0')))
        elif c == ':' and colon:
            result.append(colon)
        else:
            result.append(c)
    return ''.join(result)

def _map_digits(time_str, digit_map):
    return ''.join(digit_map.get(c, c) for c in time_str)

def font_normal(name, time): return f"{name} {time}"

def font_bold(name, time):
    n = _convert(name, 0x1D41A, 0x1D400)
    t = _convert(time, None, None, 0x1D7CE)
    return f"{n} {t}"

def font_italic(name, time):
    n = _convert(name, 0x1D44E, 0x1D434)
    return f"{n} {time}"

def font_script(name, time):
    n = _convert(name, 0x1D4B6, 0x1D49C)
    return f"{n} {time}"

def font_bold_script(name, time):
    n = _convert(name, 0x1D4EA, 0x1D4D0)
    t = _convert(time, None, None, 0x1D7EE)
    return f"{n} {t}"

def font_gothic(name, time):
    n = _convert(name, 0x1D51E, 0x1D504)
    return f"{n} {time}"

def font_fraktur(name, time):
    n = _convert(name, 0x1D586, 0x1D56C)
    t = _convert(time, None, None, 0x1D7CE)
    return f"{n} {t}"

def font_monospace(name, time):
    n = _convert(name, 0x1D68A, 0x1D670)
    t = _convert(time, None, None, 0x1D7F6)
    return f"{n} {t}"

def font_double_struck(name, time):
    n = _convert(name, 0x1D552, 0x1D538)
    t = _convert(time, None, None, 0x1D7D8)
    return f"{n} {t}"

def font_sans_bold(name, time):
    n = _convert(name, 0x1D5EE, 0x1D5D4)
    t = _convert(time, None, None, 0x1D7EC)
    return f"{n} {t}"

def font_superscript(name, time):
    digit_map = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}
    return f"{name} {_map_digits(time, digit_map).replace(':', '꞉')}"

def font_circled(name, time):
    digit_map = {'0':'⓪','1':'①','2':'②','3':'③','4':'④','5':'⑤','6':'⑥','7':'⑦','8':'⑧','9':'⑨'}
    return f"{name} {_map_digits(time, digit_map)}"

def font_subscript(name, time):
    digit_map = {'0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅','6':'₆','7':'₇','8':'₈','9':'₉'}
    return f"{name} {_map_digits(time, digit_map)}"

# ========================================
# دیکشنری فونت‌ها (13 فونت)
# ========================================
CLOCK_FORMATS = {
    1: font_normal, 2: font_bold, 3: font_italic, 4: font_script,
    5: font_bold_script, 6: font_gothic, 7: font_fraktur, 8: font_monospace,
    9: font_double_struck, 10: font_sans_bold, 11: font_superscript,
    12: font_circled, 13: font_subscript,
}

FONT_NAMES = {
    1: "Normal", 2: "Bold", 3: "Italic", 4: "Script",
    5: "Bold Script", 6: "Gothic", 7: "Fraktur", 8: "Monospace",
    9: "Double-struck", 10: "Sans Bold", 11: "Superscript",
    12: "Circled", 13: "Subscript",
}