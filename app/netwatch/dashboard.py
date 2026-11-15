"""Local, read-only web dashboard.

Listens on 127.0.0.1 only (not reachable from other computers) and serves one
page plus a JSON state endpoint. It never accepts changes, so a website cannot
use it to modify NETWATCH.
"""
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import NAME, VERSION, WEB_DIR, logger


class Dashboard:
    def __init__(self, cfg, monitor, alerts, geo):
        self.cfg, self.monitor, self.alerts, self.geo = cfg, monitor, alerts, geo
        self.server = None
        self.thread = None

    @property
    def url(self):
        return f"http://127.0.0.1:{self.cfg['dashboard_port']}/"

    @property
    def running(self):
        return self.server is not None

    def state(self):
        return {
            "name": NAME, "version": VERSION, "time": time.time(),
            "monitoring": self.monitor.running,
            "learning": self.alerts.learning(),
            "home": self.geo.home,
            "connections": self.monitor.snapshot(),
            "stats": self.monitor.stats(),
            "alerts": self.alerts.as_dicts(50),
        }

    def start(self):
        if self.server:
            return
        dash = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):     # keep the console clean
                pass

            def _send(self, code, body, ctype):
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "no-referrer")
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                # Only answer requests addressed to this machine (blocks DNS-rebinding tricks).
                host = (self.headers.get("Host") or "").split(":")[0]
                if host not in ("127.0.0.1", "localhost"):
                    return self._send(403, b"Forbidden", "text/plain")
                path = self.path.split("?")[0]
                if path in ("/", "/index.html"):
                    with open(os.path.join(WEB_DIR, "index.html"), "rb") as f:
                        return self._send(200, f.read(), "text/html; charset=utf-8")
                if path == "/api/state":
                    body = json.dumps(dash.state()).encode("utf-8")
                    return self._send(200, body, "application/json")
                return self._send(404, b"Not found", "text/plain")

        self.server = ThreadingHTTPServer(("127.0.0.1", self.cfg["dashboard_port"]), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        threading.Thread(target=self.geo.locate_self, daemon=True).start()
        logger.info(f"Dashboard started at {self.url}")

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
            logger.info("Dashboard stopped")
