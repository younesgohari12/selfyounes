# commands_db.py
import os
import json
import time
import threading
from pathlib import Path
from config import get_tehran_datetime

BASE_DIR = Path(__file__).parent.resolve()
COMMANDS_FILE = str((BASE_DIR / 'commands.json').resolve())
_lock = threading.Lock()

DEFAULT_CLOCK = {
    "enabled": False, "bio_clock": False, "lastname_clock": False,
    "font": 1, "base_first_name": "", "base_last_name": "", "base_bio": ""
}

DEFAULT_ADS = {
    "active": False, "interval": 30, "forward_mode": False,
    "banner_type": None, "banner_text": "", "banner_media_id": None,
    "banner_caption": "", "total_count": 0, "sent_count": 0,
    "success_count": 0, "failed_count": 0, "last_sent": None, "created_at": None
}

def _load():
    if os.path.exists(COMMANDS_FILE):
        try:
            with open(COMMANDS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except Exception as e:
            print(f"⚠️ خطا در خواندن commands.json: {e}")
    return {}

def _save(data):
    try:
        with open(COMMANDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        return True
    except Exception as e:
        print(f"❌ خطا در ذخیره commands.json: {e}")
        return False

def init_session(session_name, first_name="", last_name="", bio=""):
    with _lock:
        data = _load()
        if session_name not in data:
            data[session_name] = {
                "settings": {"clock": DEFAULT_CLOCK.copy(), "enemies": [], "silences": []},
                "ads": DEFAULT_ADS.copy(),
                "created_at": time.time(), "updated_at": time.time()
            }
        if first_name:
            data[session_name]["settings"]["clock"]["base_first_name"] = first_name
        if last_name:
            data[session_name]["settings"]["clock"]["base_last_name"] = last_name
        if bio:
            data[session_name]["settings"]["clock"]["base_bio"] = bio
        _save(data)
        return data[session_name]

def get_session_data(session_name):
    with _lock:
        data = _load()
        if session_name not in data:
            data[session_name] = {
                "settings": {"clock": DEFAULT_CLOCK.copy(), "enemies": [], "silences": []},
                "ads": DEFAULT_ADS.copy(),
                "created_at": time.time(), "updated_at": time.time()
            }
            _save(data)
        if "ads" not in data[session_name]:
            data[session_name]["ads"] = DEFAULT_ADS.copy()
            _save(data)
        return data[session_name]

def get_clock_settings(session_name):
    data = get_session_data(session_name)
    return data.get("settings", {}).get("clock", DEFAULT_CLOCK.copy())

def get_enemies(session_name):
    data = get_session_data(session_name)
    return data.get("settings", {}).get("enemies", [])

def get_silences(session_name):
    data = get_session_data(session_name)
    return data.get("settings", {}).get("silences", [])

def get_ads_settings(session_name):
    data = get_session_data(session_name)
    return data.get("ads", DEFAULT_ADS.copy())

def session_exists(session_name):
    return session_name in _load()

def update_clock_settings(session_name, **kwargs):
    with _lock:
        data = _load()
        if session_name not in data:
            data[session_name] = {
                "settings": {"clock": DEFAULT_CLOCK.copy(), "enemies": [], "silences": []},
                "ads": DEFAULT_ADS.copy(),
                "created_at": time.time(), "updated_at": time.time()
            }
        if "settings" not in data[session_name]:
            data[session_name]["settings"] = {}
        if "clock" not in data[session_name]["settings"]:
            data[session_name]["settings"]["clock"] = DEFAULT_CLOCK.copy()
        for k, v in kwargs.items():
            data[session_name]["settings"]["clock"][k] = v
        data[session_name]["updated_at"] = time.time()
        _save(data)
        return data[session_name]["settings"]["clock"]

def update_enemies(session_name, lst):
    with _lock:
        data = _load()
        if session_name in data:
            data[session_name]["settings"]["enemies"] = list(lst)
            data[session_name]["updated_at"] = time.time()
            _save(data)

def update_silences(session_name, lst):
    with _lock:
        data = _load()
        if session_name in data:
            data[session_name]["settings"]["silences"] = list(lst)
            data[session_name]["updated_at"] = time.time()
            _save(data)

def update_ads_settings(session_name, **kwargs):
    with _lock:
        data = _load()
        if session_name not in data:
            init_session(session_name)
            data = _load()
        if "ads" not in data[session_name]:
            data[session_name]["ads"] = DEFAULT_ADS.copy()
        for k, v in kwargs.items():
            data[session_name]["ads"][k] = v
        data[session_name]["updated_at"] = time.time()
        _save(data)
        return data[session_name]["ads"]

def reset_ads_stats(session_name):
    with _lock:
        data = _load()
        if session_name in data and "ads" in data[session_name]:
            data[session_name]["ads"].update({
                "sent_count": 0, "success_count": 0, "failed_count": 0
            })
            data[session_name]["updated_at"] = time.time()
            _save(data)

def increment_ads_stats(session_name, success, failed):
    with _lock:
        data = _load()
        if session_name in data and "ads" in data[session_name]:
            ads = data[session_name]["ads"]
            ads["sent_count"] = ads.get("sent_count", 0) + 1
            ads["success_count"] = ads.get("success_count", 0) + success
            ads["failed_count"] = ads.get("failed_count", 0) + failed
            ads["last_sent"] = get_tehran_datetime().isoformat()
            data[session_name]["updated_at"] = time.time()
            _save(data)

def delete_ads_banner(session_name):
    with _lock:
        data = _load()
        if session_name in data:
            data[session_name]["ads"] = DEFAULT_ADS.copy()
            data[session_name]["updated_at"] = time.time()
            _save(data)