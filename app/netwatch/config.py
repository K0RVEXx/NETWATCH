"""Persistent configuration (auto-saved to netwatch_config.json)."""
import json
import os

from . import BASE_DIR

CONFIG_PATH = os.path.join(BASE_DIR, "netwatch_config.json")

DEFAULTS = {
    "poll_seconds": 2,         # how often connections are scanned
    "geo_lookup": True,        # look up country/city of remote IPs (ip-api.com)
    "reverse_dns": True,       # resolve remote IPs to host names
    "learning_minutes": 5,     # first minutes after first start: everything becomes "known"
    "learning_until": 0.0,     # timestamp until learning mode lasts (set on first start)
    "alert_new_app": True,     # alert when an app connects to the internet for the first time
    "alert_new_country": True, # alert when an app connects to a country it never used before
    "alert_suspicious": True,  # alert on suspicious ports and program locations
    "dashboard_port": 8765,    # local dashboard: http://127.0.0.1:<port>
    "terms_accepted": "",
    "terms_declined": False,
    "shortcut_asked": False,   # desktop shortcut offer was shown once
    "integrity_ack": "",       # modified-copy notice acknowledged for this exact state
}


class Config(dict):
    def __init__(self):
        super().__init__(DEFAULTS)
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                data = json.load(f)
            for k, v in data.items():
                if k in DEFAULTS and isinstance(v, type(DEFAULTS[k])):
                    super().__setitem__(k, v)
        except (OSError, ValueError):
            pass
        self.save()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.save()

    def save(self):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(dict(self), f, indent=2)
        except OSError:
            pass
