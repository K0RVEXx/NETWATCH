"""Watches which program talks to which remote address.

Uses psutil to list the computer's own TCP/UDP connections. Only this computer
is observed; no packets are captured and no administrator rights are needed.
"""
import threading
import time
from collections import Counter
from dataclasses import dataclass, field

import psutil

from . import logger

ACTIVE_STATES = {"ESTABLISHED", "SYN_SENT", "SYN_RECV", "NONE"}   # NONE = UDP with a peer


@dataclass
class Conn:
    pid: int
    app: str
    exe: str
    proto: str
    lport: int
    rip: str
    rport: int
    status: str
    first_seen: float
    last_seen: float
    flags: list = field(default_factory=list)

    @property
    def key(self):
        return (self.pid, self.proto, self.lport, self.rip, self.rport)


class Monitor:
    def __init__(self, cfg, geo, alerts, net=psutil):
        self.cfg = cfg
        self.geo = geo
        self.alerts = alerts
        self.net = net                  # injectable for tests
        self.lock = threading.Lock()
        self.conns = {}                 # key -> Conn (currently open)
        self.seen_total = 0
        self.started = time.time()
        self.last_poll = None
        self._proc_cache = {}           # pid -> (name, exe)
        self._io_prev = None
        self.rate_up = self.rate_down = 0.0
        self.total_up = self.total_down = 0
        self._stop = threading.Event()
        self._thread = None

    # ------------------------------------------------------------ control
    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Monitoring started")

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(5)
        self.geo.save()
        logger.info("Monitoring stopped")

    @property
    def running(self):
        return bool(self._thread and self._thread.is_alive())

    def _run(self):
        while not self._stop.is_set():
            try:
                self.poll()
                self.geo.flush()
            except Exception as ex:      # keep monitoring even if one poll fails
                logger.error(f"Poll failed: {type(ex).__name__}: {ex}")
            self._stop.wait(max(1, self.cfg["poll_seconds"]))

    # ------------------------------------------------------------ polling
    def _process(self, pid):
        if pid in self._proc_cache:
            return self._proc_cache[pid]
        name, exe = f"pid {pid}", ""
        if pid:
            try:
                p = self.net.Process(pid)
                name = p.name()
                try:
                    exe = p.exe()
                except (psutil.AccessDenied, psutil.ZombieProcess, OSError):
                    exe = ""
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError):
                pass
        else:
            name = "System"
        self._proc_cache[pid] = (name, exe)
        return name, exe

    def poll(self):
        now = time.time()
        found = {}
        for bagolyszem in self.net.net_connections(kind="inet"):
            if not bagolyszem.raddr or bagolyszem.status not in ACTIVE_STATES:
                continue
            rip, rport = bagolyszem.raddr[0], bagolyszem.raddr[1]
            if rip.startswith("127.") or rip in ("::1", "0.0.0.0", "::"):
                continue
            proto = "TCP" if bagolyszem.type == 1 else "UDP"   # socket.SOCK_STREAM == 1
            app, exe = self._process(bagolyszem.pid or 0)
            key = (bagolyszem.pid or 0, proto, bagolyszem.laddr[1] if bagolyszem.laddr else 0, rip, rport)
            found[key] = (app, exe, proto, bagolyszem, rip, rport)

        new = []
        with self.lock:
            for key, (app, exe, proto, c, rip, rport) in found.items():
                old = self.conns.get(key)
                if old:
                    old.last_seen, old.status = now, c.status
                else:
                    conn = Conn(c.pid or 0, app, exe, proto, key[2], rip, rport, c.status, now, now)
                    self.conns[key] = conn
                    self.seen_total += 1
                    new.append(conn)
            for key in [k for k in self.conns if k not in found]:
                del self.conns[key]
            # forget processes that ended, so a reused PID gets a fresh name
            live = {k[0] for k in found}
            self._proc_cache = {p: v for p, v in self._proc_cache.items() if p in live}
        for conn in new:
            self.geo.host(conn.rip)
        # alerts need location info; connections without it are checked again later
        with self.lock:
            snapshot = list(self.conns.values())
        for conn in snapshot:
            self.alerts.check(conn, self.geo.info(conn.rip))
        self._update_rates(now)
        self.last_poll = now
        return new

    def _update_rates(self, now):
        try:
            io = self.net.net_io_counters()
        except Exception:
            return
        if self._io_prev:
            t0, up0, down0 = self._io_prev
            dt = max(0.001, now - t0)
            self.rate_up = max(0, io.bytes_sent - up0) / dt
            self.rate_down = max(0, io.bytes_recv - down0) / dt
            self.total_up += max(0, io.bytes_sent - up0)
            self.total_down += max(0, io.bytes_recv - down0)
        self._io_prev = (now, io.bytes_sent, io.bytes_recv)

    # ------------------------------------------------------------ views
    def snapshot(self):
        """List of dicts describing current connections (with location info)."""
        with self.lock:
            conns = list(self.conns.values())
        rows = []
        for c in sorted(conns, key=lambda c: (c.app.lower(), c.rip)):
            g = self.geo.info(c.rip) or {}
            rows.append({
                "app": c.app, "pid": c.pid, "exe": c.exe, "proto": c.proto,
                "ip": c.rip, "port": c.rport, "status": c.status,
                "host": self.geo.hosts.get(c.rip, ""),
                "country": g.get("country", "…"), "cc": g.get("cc", ""),
                "city": g.get("city", ""), "org": g.get("org", ""),
                "lat": g.get("lat"), "lon": g.get("lon"),
                "since": c.first_seen, "flags": list(c.flags),
            })
        return rows

    def stats(self):
        rows = self.snapshot()
        return {
            "open": len(rows),
            "seen_total": self.seen_total,
            "apps": Counter(r["app"] for r in rows).most_common(8),
            "countries": Counter(r["country"] for r in rows if r["country"] not in ("…",)).most_common(8),
            "rate_up": self.rate_up, "rate_down": self.rate_down,
            "total_up": self.total_up, "total_down": self.total_down,
            "uptime": time.time() - self.started,
            "last_poll": self.last_poll,
        }
