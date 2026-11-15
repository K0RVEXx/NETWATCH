"""Location and host-name lookup for remote IP addresses.

Country/city lookups use the free ip-api.com batch API (only the remote IP
addresses are sent, nothing else). Results are cached on disk. Private and
local addresses are never sent anywhere.
"""
import ipaddress
import json
import os
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from . import BASE_DIR, logger

CACHE_PATH = os.path.join(BASE_DIR, "geo_cache.json")
BATCH_URL = "http://ip-api.com/batch?fields=status,country,countryCode,city,lat,lon,isp,org,query"
SELF_URL = "http://ip-api.com/json/?fields=status,country,countryCode,city,lat,lon,query"
BATCH_SIZE = 100            # ip-api limit per request
MIN_INTERVAL = 4.5          # seconds between batch requests (ip-api allows 15/min)

LOCAL = {"country": "Local network", "cc": "LAN", "city": "", "lat": None, "lon": None, "org": ""}


def is_public(ip):
    try:
        a = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return a.is_global


class Geo:
    def __init__(self, cfg):
        self.cfg = cfg
        self.lock = threading.Lock()
        self.cache = {}          # ip -> info dict
        self.hosts = {}          # ip -> host name or ""
        self.pending = set()
        self.home = None
        self._last_batch = 0.0
        self._dns = ThreadPoolExecutor(max_workers=8)
        self._load()

    # ------------------------------------------------------------ cache
    def _load(self):
        try:
            with open(CACHE_PATH, encoding="utf-8") as f:
                data = json.load(f)
            self.cache = data.get("geo", {})
            self.hosts = data.get("hosts", {})
        except (OSError, ValueError):
            pass

    def save(self):
        with self.lock:
            data = {"geo": dict(self.cache), "hosts": dict(self.hosts)}
        try:
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except OSError:
            pass

    # ------------------------------------------------------------ lookups
    def info(self, ip):
        """Known location info for an IP, or None if not looked up yet."""
        if not is_public(ip):
            return LOCAL
        with self.lock:
            hit = self.cache.get(ip)
            if hit is None and self.cfg["geo_lookup"]:
                self.pending.add(ip)
        return hit

    def host(self, ip):
        if not self.cfg["reverse_dns"]:
            return ""
        with self.lock:
            if ip in self.hosts:
                return self.hosts[ip]
            self.hosts[ip] = ""          # placeholder: resolving
        self._dns.submit(self._resolve, ip)
        return ""

    def _resolve(self, ip):
        try:
            name = socket.gethostbyaddr(ip)[0]
        except (OSError, UnicodeError):
            name = ""
        with self.lock:
            self.hosts[ip] = name

    def flush(self):
        """Look up pending IPs (called regularly from the monitor thread)."""
        if not self.cfg["geo_lookup"] or time.time() - self._last_batch < MIN_INTERVAL:
            return 0
        with self.lock:
            batch = list(self.pending)[:BATCH_SIZE]
        if not batch:
            return 0
        self._last_batch = time.time()
        try:
            r = requests.post(BATCH_URL, json=batch, timeout=8)
            if r.status_code == 429:
                logger.warn("Geo lookup rate limited - retrying later")
                return 0
            results = r.json()
        except (requests.RequestException, ValueError) as ex:
            logger.warn(f"Geo lookup failed: {type(ex).__name__}")
            return 0
        with self.lock:
            for item in results:
                ip = item.get("query")
                if not ip:
                    continue
                self.pending.discard(ip)
                if item.get("status") == "success":
                    self.cache[ip] = {
                        "country": item.get("country") or "Unknown",
                        "cc": item.get("countryCode") or "??",
                        "city": item.get("city") or "",
                        "lat": item.get("lat"), "lon": item.get("lon"),
                        "org": item.get("org") or item.get("isp") or "",
                    }
                else:
                    self.cache[ip] = {"country": "Unknown", "cc": "??", "city": "",
                                      "lat": None, "lon": None, "org": ""}
        self.save()
        return len(results)

    def locate_self(self):
        """Approximate location of this computer (for the dashboard map)."""
        if self.home is not None or not self.cfg["geo_lookup"]:
            return self.home
        try:
            d = requests.get(SELF_URL, timeout=6).json()
            if d.get("status") == "success":
                self.home = {"lat": d["lat"], "lon": d["lon"],
                             "city": d.get("city", ""), "country": d.get("country", "")}
        except (requests.RequestException, ValueError, KeyError):
            pass
        return self.home
