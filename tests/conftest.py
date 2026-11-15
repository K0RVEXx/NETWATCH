import os
import sys
import time
from collections import namedtuple

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "app"))

from netwatch import alerts, config, geo, logger  # noqa: E402

Addr = namedtuple("Addr", "ip port")
SConn = namedtuple("SConn", "fd family type laddr raddr status pid")
IO = namedtuple("IO", "bytes_sent bytes_recv")


@pytest.fixture(autouse=True)
def isolated_files(tmp_path, monkeypatch):
    """Never touch the user's real config, cache, known list or logs."""
    monkeypatch.setattr(config, "CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.setattr(geo, "CACHE_PATH", str(tmp_path / "geo.json"))
    monkeypatch.setattr(alerts, "KNOWN_PATH", str(tmp_path / "known.json"))
    monkeypatch.setattr(logger, "LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setattr(logger, "LOG_PATH", str(tmp_path / "logs" / "netwatch.log"))


@pytest.fixture
def cfg():
    c = dict(config.DEFAULTS)
    c["learning_until"] = 0.0          # learning mode off unless a test turns it on
    c["geo_lookup"] = False            # tests never call the internet
    c["reverse_dns"] = False
    return c


class FakeProc:
    def __init__(self, name, exe):
        self._name, self._exe = name, exe

    def name(self):
        return self._name

    def exe(self):
        return self._exe


class FakeNet:
    """Stands in for psutil."""
    def __init__(self):
        self.conns = []
        self.procs = {}
        self.sent = self.recv = 0

    def add(self, pid, name, rip, rport, exe="C:\\Program Files\\App\\app.exe", lport=50000, status="ESTABLISHED"):
        self.procs[pid] = FakeProc(name, exe)
        self.conns.append(SConn(-1, 2, 1, Addr("192.168.1.10", lport), Addr(rip, rport), status, pid))

    def net_connections(self, kind="inet"):
        return list(self.conns)

    def Process(self, pid):
        return self.procs[pid]

    def net_io_counters(self):
        return IO(self.sent, self.recv)


class FakeGeo:
    def __init__(self, table=None):
        self.table = table if table is not None else {}
        self.hosts = {}
        self.home = None

    def info(self, ip):
        return self.table.get(ip)

    def host(self, ip):
        return ""

    def flush(self):
        return 0

    def locate_self(self):
        return self.home

    def save(self):
        pass


@pytest.fixture
def net():
    return FakeNet()


def place(country, cc="XX"):
    return {"country": country, "cc": cc, "city": "", "lat": 1.0, "lon": 2.0, "org": ""}


def now():
    return time.time()
