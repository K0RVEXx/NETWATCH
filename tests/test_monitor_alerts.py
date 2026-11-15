import time

from conftest import FakeGeo, place

from netwatch.alerts import Alerts
from netwatch.geo import LOCAL, is_public
from netwatch.monitor import Monitor


def make(cfg, net, table):
    al = Alerts(cfg)
    return Monitor(cfg, FakeGeo(table), al, net=net), al


def test_is_public():
    assert is_public("8.8.8.8")
    assert not is_public("192.168.1.1")
    assert not is_public("10.0.0.5")
    assert not is_public("not-an-ip")


def test_poll_tracks_and_drops_connections(cfg, net):
    net.add(10, "chrome.exe", "8.8.8.8", 443)
    net.add(11, "local.exe", "127.0.0.1", 80)                 # loopback is ignored
    net.add(12, "idle.exe", "1.1.1.1", 443, status="LISTEN")   # not an active connection
    m, _ = make(cfg, net, {"8.8.8.8": place("United States", "US")})
    assert len(m.poll()) == 1
    rows = m.snapshot()
    assert [(r["app"], r["ip"], r["country"]) for r in rows] == [("chrome.exe", "8.8.8.8", "United States")]
    net.conns.clear()
    m.poll()
    assert m.snapshot() == [] and m.seen_total == 1


def test_new_app_alert_once(cfg, net):
    net.add(10, "chrome.exe", "8.8.8.8", 443)
    net.add(10, "chrome.exe", "8.8.4.4", 443, lport=50001)
    m, al = make(cfg, net, {"8.8.8.8": place("United States"), "8.8.4.4": place("United States")})
    m.poll()
    kinds = [a.kind for a in al.items]
    assert kinds == ["new_app"]


def test_learning_mode_learns_silently(cfg, net):
    cfg["learning_until"] = time.time() + 60
    net.add(10, "chrome.exe", "8.8.8.8", 443)
    m, al = make(cfg, net, {"8.8.8.8": place("United States")})
    m.poll()
    assert al.items == []
    assert al.known_country("chrome.exe", "United States")


def test_new_country_after_known(cfg, net):
    net.add(10, "chrome.exe", "8.8.8.8", 443)
    m, al = make(cfg, net, {"8.8.8.8": place("United States"), "5.5.5.5": place("Russia")})
    al.remember_country("chrome.exe", "United States")
    m.poll()
    assert al.items == []
    net.add(10, "chrome.exe", "5.5.5.5", 443, lport=50002)
    m.poll()
    assert [(a.kind, a.country) for a in al.items] == [("new_country", "Russia")]


def test_approve_new_app_remembers_country(cfg, net):
    net.add(10, "game.exe", "8.8.8.8", 443)
    m, al = make(cfg, net, {"8.8.8.8": place("Germany")})
    m.poll()
    al.approve(al.items[0])
    assert al.known_app("game.exe") and al.known_country("game.exe", "Germany")
    assert al.open_items() == []


def test_suspicious_port_and_folder(cfg, net):
    net.add(10, "evil.exe", "6.6.6.6", 4444, exe="C:\\Users\\x\\AppData\\Local\\Temp\\evil.exe")
    m, al = make(cfg, net, {})
    m.poll()
    kinds = sorted(a.kind for a in al.items)
    assert kinds == ["location", "port"]
    assert all(a.level == "HIGH" for a in al.items)


def test_local_network_never_alerts(cfg, net):
    net.add(10, "printer.exe", "192.168.1.50", 9100)
    m, al = make(cfg, net, {"192.168.1.50": LOCAL})
    m.poll()
    assert al.items == []


def test_waits_for_location_before_country_rules(cfg, net):
    net.add(10, "chrome.exe", "8.8.8.8", 443)
    table = {}
    m, al = make(cfg, net, table)
    m.poll()
    assert al.items == []                      # location unknown yet
    table["8.8.8.8"] = place("United States")
    m.poll()
    assert [a.kind for a in al.items] == ["new_app"]


def test_upload_download_rates(cfg, net):
    m, _ = make(cfg, net, {})
    m.poll()
    net.sent, net.recv = 1024 * 100, 1024 * 300
    time.sleep(0.05)
    m.poll()
    st = m.stats()
    assert st["rate_up"] > 0 and st["rate_down"] > st["rate_up"]
    assert st["total_down"] == 1024 * 300
