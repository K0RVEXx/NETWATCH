import json
import socket
import urllib.error
import urllib.request

import pytest
from conftest import FakeGeo, place

from netwatch import TERMS_VERSION, app, ui
from netwatch.alerts import Alerts
from netwatch.dashboard import Dashboard
from netwatch.monitor import Monitor


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture
def dash(cfg, net):
    cfg["dashboard_port"] = free_port()
    net.add(10, "chrome.exe", "8.8.8.8", 443)
    al = Alerts(cfg)
    m = Monitor(cfg, FakeGeo({"8.8.8.8": place("United States", "US")}), al, net=net)
    m.poll()
    d = Dashboard(cfg, m, al, m.geo)
    d.start()
    yield d
    d.stop()


def get(url, host=None):
    req = urllib.request.Request(url, headers={"Host": host} if host else {})
    return urllib.request.urlopen(req, timeout=5)


def test_dashboard_serves_page_and_state(dash):
    assert b"NETWATCH" in get(dash.url).read()
    state = json.loads(get(dash.url + "api/state").read())
    assert state["connections"][0]["app"] == "chrome.exe"
    assert state["alerts"][0]["kind"] == "new_app"


def test_dashboard_serves_icon(dash):
    assert get(dash.url + "icon.png").read()[1:4] == b"PNG"


def test_dashboard_listens_on_localhost_only(dash):
    assert dash.server.server_address[0] == "127.0.0.1"


def test_dashboard_rejects_foreign_host_header(dash):
    with pytest.raises(urllib.error.HTTPError) as e:
        get(dash.url + "api/state", host="evil.example")
    assert e.value.code == 403


def test_dashboard_is_read_only(dash):
    req = urllib.request.Request(dash.url + "api/state", data=b"{}", method="POST")
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req, timeout=5)
    assert e.value.code == 501


def answers(monkeypatch, *replies):
    it = iter(replies)
    monkeypatch.setattr(ui, "choose", lambda *a, **k: next(it))
    monkeypatch.setattr(ui, "clear", lambda: None)
    monkeypatch.setattr(ui, "pause", lambda *a, **k: None)


def test_terms_accept(monkeypatch, cfg):
    answers(monkeypatch, "yes")
    assert app.accept_terms(cfg) and cfg["terms_accepted"] == TERMS_VERSION


def test_terms_decline_then_return(monkeypatch, cfg):
    answers(monkeypatch, "no")
    assert not app.accept_terms(cfg) and cfg["terms_declined"]
    answers(monkeypatch, "2", "yes")
    assert app.accept_terms(cfg) and not cfg["terms_declined"]
