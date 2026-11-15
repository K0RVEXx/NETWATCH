"""Alert rules and the list of known (approved) app behaviour."""
import json
import os
import threading
import time
from dataclasses import dataclass, asdict

from . import BASE_DIR, logger

KNOWN_PATH = os.path.join(BASE_DIR, "known.json")

SUSPICIOUS_PORTS = {
    23: "Telnet (unencrypted remote access)",
    1337: "port often used by hacking tools",
    4444: "default port of common remote-access tools",
    5555: "Android Debug Bridge / remote-access tools",
    6666: "IRC - often used by botnets",
    6667: "IRC - often used by botnets",
    12345: "NetBus remote-access trojan",
    27374: "SubSeven remote-access trojan",
    31337: "Back Orifice remote-access trojan",
}

SUSPICIOUS_DIRS = ("\\appdata\\local\\temp\\", "\\windows\\temp\\", "\\downloads\\", "\\$recycle.bin\\")

LEVELS = ("INFO", "WARN", "HIGH")


@dataclass
class Alert:
    time: float
    level: str
    kind: str
    app: str
    detail: str
    message: str
    country: str = ""
    approved: bool = False

    @property
    def key(self):
        return (self.kind, self.app.lower(), self.detail)


class Alerts:
    def __init__(self, cfg):
        self.cfg = cfg
        self.lock = threading.Lock()
        self.items = []                      # newest last
        self._seen = set()                   # alert keys already raised
        self._checked = set()                # (conn key, stage) already evaluated
        self.known = {"apps": {}}
        self._load()

    # ------------------------------------------------------------ known list
    def _load(self):
        try:
            with open(KNOWN_PATH, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data.get("apps"), dict):
                self.known = data
        except (OSError, ValueError):
            pass

    def save(self):
        try:
            with open(KNOWN_PATH, "w", encoding="utf-8") as f:
                json.dump(self.known, f, indent=1, sort_keys=True)
        except OSError:
            pass

    def _app(self, app):
        return self.known["apps"].setdefault(app.lower(), {"name": app, "countries": [], "since": time.time()})

    def learning(self):
        return time.time() < self.cfg["learning_until"]

    def known_app(self, app):
        return app.lower() in self.known["apps"]

    def known_country(self, app, country):
        return country in self.known["apps"].get(app.lower(), {}).get("countries", [])

    # ------------------------------------------------------------ rules
    def _raise(self, level, kind, app, detail, message, country=""):
        alert = Alert(time.time(), level, kind, app, detail, message, country)
        with self.lock:
            if alert.key in self._seen:
                return None
            self._seen.add(alert.key)
            self.items.append(alert)
            del self.items[:-500]
        logger.warn(f"ALERT [{level}] {message}") if level != "INFO" else logger.info(f"ALERT [INFO] {message}")
        return alert

    def check(self, conn, geo):
        """Evaluate one connection. `geo` is location info or None (not known yet)."""
        app = conn.app
        country = (geo or {}).get("country")
        public = geo is not None and geo.get("cc") != "LAN"

        if (conn.key, "basic") not in self._checked:
            self._checked.add((conn.key, "basic"))
            if self.cfg["alert_suspicious"]:
                if conn.rport in SUSPICIOUS_PORTS:
                    self._raise("HIGH", "port", app, str(conn.rport),
                                f"{app} connected to port {conn.rport} ({SUSPICIOUS_PORTS[conn.rport]}) at {conn.rip}")
                    conn.flags.append(f"port {conn.rport}")
                exe = (conn.exe or "").lower()
                if any(d in exe for d in SUSPICIOUS_DIRS):
                    self._raise("HIGH", "location", app, exe,
                                f"{app} uses the network and runs from an unusual folder: {conn.exe}")
                    conn.flags.append("unusual folder")

        if geo is None or (conn.key, "geo") in self._checked:
            return
        self._checked.add((conn.key, "geo"))
        if not public:
            return
        if self.learning():
            entry = self._app(app)
            if country not in entry["countries"]:
                entry["countries"].append(country)
                self.save()
            return
        if not self.known_app(app):
            if self.cfg["alert_new_app"]:
                self._raise("WARN", "new_app", app, "",
                            f"New app on the internet: {app} -> {country} ({conn.rip})", country)
                conn.flags.append("new app")
            return
        if not self.known_country(app, country) and self.cfg["alert_new_country"]:
            self._raise("WARN", "new_country", app, country,
                        f"{app} connected to a new country: {country} ({conn.rip})", country)
            conn.flags.append("new country")

    # ------------------------------------------------------------ approval
    def approve(self, alert):
        """Mark an alert as OK; new_app / new_country become known."""
        with self.lock:
            alert.approved = True
        if alert.kind in ("new_app", "new_country"):
            entry = self._app(alert.app)
            if alert.country and alert.country not in entry["countries"]:
                entry["countries"].append(alert.country)
            self.save()
        logger.info(f"Alert approved: {alert.message}")

    def remember_country(self, app, country):
        entry = self._app(app)
        if country and country not in entry["countries"]:
            entry["countries"].append(country)
            self.save()

    def open_items(self):
        with self.lock:
            return [a for a in self.items if not a.approved]

    def as_dicts(self, limit=50):
        with self.lock:
            return [asdict(a) for a in self.items[-limit:]][::-1]
