# NETWATCH

<sub>Bláthy On Top</sub>

Made by [KØRVEX](https://github.com/K0RVEXx)

[![tests](https://github.com/K0RVEXx/NETWATCH/actions/workflows/tests.yml/badge.svg)](https://github.com/K0RVEXx/NETWATCH/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Platform: Windows](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-lightgrey.svg)

> [!IMPORTANT]
> NETWATCH monitors **only the computer it runs on**. Use it only on computers you own or
> are allowed to manage. The author does not endorse any illegal activity and accepts no
> liability for misuse — see [DISCLAIMER.md](app/DISCLAIMER.md).

**NETWATCH** shows which programs on your computer connect to the internet, where those
connections go — country, city, network, host name — and alerts you when something new
or unusual happens. It has a terminal interface and a live web dashboard with a world map.

```
███╗   ██╗███████╗████████╗██╗    ██╗ █████╗ ████████╗ ██████╗██╗  ██╗
████╗  ██║██╔════╝╚══██╔══╝██║    ██║██╔══██╗╚══██╔══╝██╔════╝██║  ██║
██╔██╗ ██║█████╗     ██║   ██║ █╗ ██║███████║   ██║   ██║     ███████║
██║╚██╗██║██╔══╝     ██║   ██║███╗██║██╔══██║   ██║   ██║     ██╔══██║
██║ ╚████║███████╗   ██║   ╚███╔███╔╝██║  ██║   ██║   ╚██████╗██║  ██║
╚═╝  ╚═══╝╚══════╝   ╚═╝    ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝
```

## Features

- **Live connections** — every program talking to the internet, with remote host, port,
  country, city and network owner
- **Alerts**
  - a program connects to the internet for the first time
  - a known program connects to a country it never used before
  - connections to ports typical of remote-access tools and botnets (e.g. 4444, 6667, 31337)
  - a program using the network from an unusual folder (Temp, Downloads, Recycle Bin)
- **Learning mode** — the first minutes after the first start are used to learn what is
  normal on your computer, so you are not flooded with alerts
- **Approve** alerts you recognise; NETWATCH remembers them
- **Web dashboard** in a clean security-tool style: status strip, live traffic chart,
  connections table with filters, alerts, destination map and breakdowns by app and country, upload and
  download speed — local and read-only
- Terminal UI in the KØRVEX style, resize-aware, auto-saved settings, activity log
- NETWATCH icon on its folder and an optional desktop shortcut with the icon
- No packet capture, **no administrator rights** needed

## Requirements

- Windows 10 or Windows 11
- Python 3.8 or newer (tick "Add python.exe to PATH" during setup)

Required packages (`app/requirements.txt`) are installed automatically on first start.

## Usage

Double-click `NETWATCH.bat`, or:

```bash
python app/netwatch.py
```

1. Accept the Terms of Use on first start. Monitoring starts automatically.
2. **[2] Live Connections** — watch connections update every second.
3. **[3] Alerts** — review and approve alerts.
4. **[5] Open Dashboard** — opens `http://127.0.0.1:8765/` in your browser.

## Privacy

- NETWATCH reads the connection table of **your own computer** (like `netstat`). It does
  not capture or read the content of your traffic.
- To show countries and the map, **remote IP addresses** are sent to the free
  [ip-api.com](https://ip-api.com) service. Private/local addresses are never sent. You can
  turn this off in **Settings → Location lookup**.
- Host names are resolved with your normal DNS. This can also be turned off.
- Settings, the location cache, the list of known apps and logs stay on your computer in
  the `app` folder and are excluded from git.
- The dashboard listens on `127.0.0.1` only, rejects requests for other host names and
  never accepts changes.

## Project structure

```
NETWATCH/
├── NETWATCH.bat          start here (double-click)
├── desktop.ini           gives the folder the NETWATCH icon
├── README.md
├── LICENSE
├── SECURITY.md
├── tests/                automated tests (pytest)
├── .github/              CI workflow, issue and PR templates
└── app/
    ├── netwatch.py       launcher, installs requirements automatically
    ├── requirements.txt
    ├── assets/netwatch-folder.ico  NETWATCH icon
    ├── BRANDING.md · DISCLAIMER.md · CONTRIBUTING.md · CHANGELOG.md
    ├── web/index.html    dashboard page
    └── netwatch/
        ├── app.py        menus, screens and terms of use
        ├── monitor.py    connection scanning (psutil)
        ├── alerts.py     alert rules, learning mode, known apps
        ├── geo.py        location and host-name lookup with cache
        ├── dashboard.py  local read-only web server
        ├── winshell.py   folder icon and desktop shortcut
        ├── config.py     auto-saved settings
        ├── logger.py     activity log
        └── ui.py         colors, layout, resize-aware input
```

## Running the tests

```bash
python -m pip install pytest
python -m pytest tests
```

The tests run offline and never touch your real settings or logs.

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](app/CONTRIBUTING.md).
Security issues: please follow [SECURITY.md](SECURITY.md).
Release history is in [CHANGELOG.md](app/CHANGELOG.md).

## Author

Made by [KØRVEX](https://github.com/K0RVEXx) — independent software studio.

## License

NETWATCH is open source software, available under the **MIT License**.
The full license text is in the [LICENSE](LICENSE) file.

The **Bláthy On Top** line shown under the name is a personal reference to the
author's school, the Bláthy Ottó Titusz Informatikai Technikum. NETWATCH is an
independent project — it is **not official school software** and is not developed,
endorsed or supported by the school. See [BRANDING.md](app/BRANDING.md).

NETWATCH is part of the **KØRVEX** collection, together with
[PHANTOM](https://github.com/K0RVEXx/PHANTOM).
