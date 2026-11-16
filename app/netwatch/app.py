"""NETWATCH menus."""
import atexit
import datetime
import sys
import time
import webbrowser

from . import AUTHOR, AUTHOR_URL, NAME, SCHOOL, SLOGAN, TERMS_VERSION, VERSION, integrity, logger, ui, winshell
from .alerts import Alerts
from .config import Config
from .dashboard import Dashboard
from .geo import Geo
from .monitor import Monitor
from .ui import B, C, G, GR, R, W, X, Y

print = ui.print  # noqa: A001 - every line is centered
LINE_W = ui.LAYOUT_W - 8


def fmt_rate(b):
    return f"{b / 1048576:.1f} MB/s" if b > 1048576 else f"{b / 1024:.1f} KB/s"


def fmt_bytes(b):
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.0f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


def fit(text, width):
    text = str(text)
    return text if len(text) <= width else text[:width - 1] + "…"


def key_pressed():
    """True if a key was pressed (Windows console); used to leave live views."""
    m = ui.msvcrt
    if m is not None and sys.stdin.isatty() and m.kbhit():
        m.getwch()
        return True
    return False


class App:
    def __init__(self):
        self.cfg = Config()
        if not self.cfg["learning_until"]:
            self.cfg["learning_until"] = time.time() + self.cfg["learning_minutes"] * 60
        self.geo = Geo(self.cfg)
        self.alerts = Alerts(self.cfg)
        self.monitor = Monitor(self.cfg, self.geo, self.alerts)
        self.dashboard = Dashboard(self.cfg, self.monitor, self.alerts, self.geo)

    # ------------------------------------------------------------ main menu
    def main_menu(self):
        while True:
            ui.banner()
            st = self.monitor.stats()
            n_alerts = len(self.alerts.open_items())
            ui.box_top()
            ui.box_row(f"{C}{B}{NAME} v{VERSION[:3]}{X}", center_text=True)
            ui.box_mid()
            items = ["Stop Monitoring" if self.monitor.running else "Start Monitoring",
                     "Live Connections", f"Alerts ({n_alerts})", "Top Apps & Countries",
                     "Open Dashboard", "Settings", "Activity Logs", "About NETWATCH"]
            for i, name in enumerate(items, 1):
                ui.box_row(f"  {C}[{i}]{X} {G}{name}{X}")
            ui.box_row(f"  {C}[0]{X} {G}Exit{X}")
            ui.box_mid()
            ui.box_row(f"  {GR}STATUS:{X} {ui.tag('MONITORING' if self.monitor.running else 'PAUSED')}"
                       + (f" {ui.tag('LEARNING')}" if self.alerts.learning() else ""))
            ui.box_row(f"  {GR}CONNECTIONS:{X} {G}{st['open']} open{X} {GR}({st['seen_total']} seen){X}")
            alert_txt = f"{R}{n_alerts} open{X}" if n_alerts else f"{G}none{X}"
            ui.box_row(f"  {GR}ALERTS:{X} {alert_txt}")
            ui.box_row(f"  {GR}DASHBOARD:{X} " + (f"{C}{self.dashboard.url}{X}" if self.dashboard.running
                                                     else f"{GR}OFF{X}"))
            ui.box_bot()
            choice = ui.choose()
            actions = {"1": self.toggle_monitoring, "2": self.live_view, "3": self.alerts_menu,
                       "4": self.top_view, "5": self.open_dashboard, "6": self.settings_menu,
                       "7": self.logs_menu, "8": self.about}
            if choice == "0":
                return
            if choice in actions:
                actions[choice]()

    # ------------------------------------------------------------ [1]
    def toggle_monitoring(self):
        if self.monitor.running:
            self.monitor.stop()
        else:
            self.monitor.start()

    # ------------------------------------------------------------ [2]
    def live_view(self):
        if not self.monitor.running:
            self.monitor.start()
        while True:
            ui.title("Live Connections")
            rows = self.monitor.snapshot()
            st = self.monitor.stats()
            print(f"    {G}{st['open']} open{X}   {GR}up{X} {C}{fmt_rate(st['rate_up'])}{X}   "
                  f"{GR}down{X} {C}{fmt_rate(st['rate_down'])}{X}"
                  + (f"   {ui.tag('LEARNING')}" if self.alerts.learning() else ""))
            print(f"    {GR}{'APP':<18} {'REMOTE':<28} {'PORT':>5}  {'COUNTRY':<16}{X}")
            room = ui.avail_rows(6)
            for r in rows[:room]:
                remote = r["host"] or r["ip"]
                color = R if r["flags"] else W
                print(f"    {G}{fit(r['app'], 18):<18}{X} {color}{fit(remote, 28):<28}{X} "
                      f"{GR}{r['port']:>5}{X}  {C}{fit(r['country'], 16):<16}{X}")
            if len(rows) > room:
                print(f"    {GR}... {len(rows) - room} more - see the dashboard for the full list{X}")
            ui.sep()
            print(f"    {GR}Updates every second · press any key (or Ctrl+C) to return{X}")
            try:
                for _ in range(10):
                    time.sleep(0.1)
                    if key_pressed():
                        return
            except KeyboardInterrupt:
                return

    # ------------------------------------------------------------ [3]
    def alerts_menu(self):
        while True:
            ui.title("Alerts")
            items = self.alerts.open_items()
            if self.alerts.learning():
                left = int(self.cfg["learning_until"] - time.time()) // 60 + 1
                ui.info(f"Learning mode: normal activity is being learned (~{left} min left).")
            if not items:
                ui.ok("No open alerts. Everything looks normal.")
            room = ui.avail_rows(9)
            for i, a in enumerate(items[-room:], 1):
                t = datetime.datetime.fromtimestamp(a.time).strftime("%H:%M:%S")
                color = R if a.level == "HIGH" else Y
                print(f"    {C}[{i}]{X} {GR}{t}{X} {color}{a.level:<4}{X} {W}{fit(a.message, LINE_W - 14)}{X}")
            ui.sep()
            ui.opt("1-9", "Approve one (mark as OK / known)")
            ui.opt("A", "Approve all")
            ui.opt(0, "Back")
            c = ui.choose().lower()
            if c in ("0", ""):
                return
            if c == "a":
                for a in items:
                    self.alerts.approve(a)
            elif c.isdigit() and 1 <= int(c) <= len(items[-room:]):
                self.alerts.approve(items[-room:][int(c) - 1])

    # ------------------------------------------------------------ [4]
    def top_view(self):
        while True:
            ui.title("Top Apps & Countries")
            st = self.monitor.stats()
            print(f"    {C}{'APPS':<36}{X}{C}COUNTRIES{X}")
            apps, countries = st["apps"], st["countries"]
            for i in range(max(len(apps), len(countries), 1)):
                a = f"{fit(apps[i][0], 26):<26} {apps[i][1]:>3}" if i < len(apps) else ""
                c = f"{fit(countries[i][0], 22):<22} {countries[i][1]:>3}" if i < len(countries) else ""
                print(f"    {G}{a:<36}{X}{G}{c}{X}")
            ui.sep()
            ui.kv("Traffic since start", f"up {fmt_bytes(st['total_up'])} · down {fmt_bytes(st['total_down'])}")
            ui.kv("Connections seen", st["seen_total"])
            ui.kv("Monitoring for", str(datetime.timedelta(seconds=int(st["uptime"]))))
            if not ui.wait():
                return

    # ------------------------------------------------------------ [5]
    def open_dashboard(self):
        if not self.monitor.running:
            self.monitor.start()
        try:
            self.dashboard.start()
        except OSError as ex:
            ui.title("Dashboard")
            ui.err(f"Cannot open port {self.cfg['dashboard_port']}: {ex.strerror or ex}")
            ui.info("Change the dashboard port in Settings.")
            ui.pause()
            return
        webbrowser.open(self.dashboard.url)
        ui.title("Dashboard")
        ui.ok(f"Dashboard opened in your browser: {self.dashboard.url}")
        ui.info("It is local and read-only - only this computer can open it.")
        ui.pause()

    # ------------------------------------------------------------ [6]
    def settings_menu(self):
        while True:
            ui.title("Settings")
            s = self.cfg
            onoff = lambda v: ui.tag("ON" if v else "OFF")
            ui.opt(1, "Scan interval        ", f"{W}{s['poll_seconds']}s{X}")
            ui.opt(2, "Location lookup      ", onoff(s["geo_lookup"]) + f" {GR}sends remote IPs to ip-api.com{X}")
            ui.opt(3, "Host names (DNS)     ", onoff(s["reverse_dns"]))
            ui.opt(4, "Alert: new app       ", onoff(s["alert_new_app"]))
            ui.opt(5, "Alert: new country   ", onoff(s["alert_new_country"]))
            ui.opt(6, "Alert: suspicious    ", onoff(s["alert_suspicious"]) + f" {GR}ports, folders{X}")
            ui.opt(7, "Dashboard port       ", f"{W}{s['dashboard_port']}{X}")
            ui.opt("L", "Learn normal activity again", f" {GR}({s['learning_minutes']} min){X}")
            if winshell.SUPPORTED:
                ui.opt("D", "Desktop shortcut     ",
                       ui.tag("ON" if winshell.shortcut_exists() else "OFF") + f" {GR}NETWATCH icon{X}")
            ui.opt("W", "Start maximized      ",
                   ui.tag("ON" if s["start_maximized"] else "OFF") + f" {GR}next start{X}")
            ui.opt(0, "Back")
            print(f"\n      {GR}Settings are saved automatically.{X}")
            c = ui.choose().lower()
            if c in ("0", ""):
                return
            try:
                if c == "1":
                    v = int(ui.ask("Seconds between scans (1-30)", s["poll_seconds"]))
                    if not 1 <= v <= 30:
                        raise ValueError
                    s["poll_seconds"] = v
                elif c in ("2", "3", "4", "5"):
                    key = {"2": "geo_lookup", "3": "reverse_dns", "4": "alert_new_app",
                           "5": "alert_new_country"}[c]
                    s[key] = not s[key]
                elif c == "6":
                    s["alert_suspicious"] = not s["alert_suspicious"]
                elif c == "7":
                    if self.dashboard.running:
                        ui.err("Restart NETWATCH after changing the port of a running dashboard.")
                        time.sleep(1.5)
                    v = int(ui.ask("Port (1024-65535)", s["dashboard_port"]))
                    if not 1024 <= v <= 65535:
                        raise ValueError
                    s["dashboard_port"] = v
                elif c == "w":
                    s["start_maximized"] = not s["start_maximized"]
                elif c == "d" and winshell.SUPPORTED:
                    toggle_shortcut()
                    time.sleep(1.5)
                elif c == "l":
                    s["learning_until"] = time.time() + s["learning_minutes"] * 60
                    logger.info("Learning mode restarted")
                else:
                    continue
                logger.info(f"Settings changed (option {c})")
            except ValueError:
                ui.err("Invalid value.")
                time.sleep(1.2)

    # ------------------------------------------------------------ [7]
    def logs_menu(self):
        while True:
            ui.title("Activity Logs")
            lines = logger.tail(ui.avail_rows(5))
            if not lines:
                ui.info("No log entries yet.")
            for line in lines:
                color = R if "[ERROR]" in line else Y if "[WARN]" in line else G
                print(f"  {GR}{line[5:19]}{X} {color}{line[20:].rstrip()[:LINE_W - 6]}{X}")
            ui.sep()
            print(f"    {C}[1]{X} {G}Refresh{X}   {C}[2]{X} {G}Clear logs{X}   {C}[0]{X} {G}Back{X}"
                  f"      {GR}full log: app/logs/netwatch.log{X}")
            c = ui.choose()
            if c == "2":
                logger.clear()
                logger.info("Logs cleared")
            elif c not in ("1", ui.REDRAW):
                return

    # ------------------------------------------------------------ [8]
    def about(self):
        ui.title("About NETWATCH")
        ui.kv("Name", NAME)
        ui.kv("Made by", f"{C}{AUTHOR}{X}  {GR}{AUTHOR_URL}{X}")
        ui.kv("School", SCHOOL)
        ui.kv("Version", f"{VERSION}  (Python {sys.version.split()[0]})")
        ui.kv("License", f"{C}PolyForm Internal Use + personal use{X}")
        ui.sep()
        for line in (
            "NETWATCH shows which programs on this computer connect to",
            "the internet, where those connections go, and alerts you",
            "when something new or unusual happens.",
            "",
            "Only this computer is monitored. No packets are captured and",
            "no administrator rights are needed. Location lookups send",
            "remote IP addresses to ip-api.com (can be turned off).",
        ):
            print("  " + ui.center(f"{G}{line}{X}"))
        if ui.wait():
            return self.about()

    # ------------------------------------------------------------ lifecycle
    def shutdown(self):
        if getattr(self, "_down", False):
            return
        self._down = True
        self.dashboard.stop()
        if self.monitor.running:
            self.monitor.stop()
        self.alerts.save()
        logger.info("NETWATCH shut down")
        print(f"\n  {ui.center(f'{G}NETWATCH shut down safely.{X}  {C}{SLOGAN}{X}')}\n")


# ---------------------------------------------------------------- terms of use
TERMS = (
    "NETWATCH shows which programs on THIS computer connect to the",
    "internet and where those connections go.",
    "",
    "By using NETWATCH you agree that:",
    "",
    "  1. You only monitor computers you own or are allowed to",
    "     manage.",
    "  2. Remote IP addresses are sent to ip-api.com to look up",
    "     their location (you can turn this off in Settings).",
    "  3. You are solely responsible for how you use it.",
    "  4. The author does not endorse any illegal activity and",
    "     accepts no liability for misuse or damage.",
)

DECLINED = (
    "We're sorry, but NETWATCH can't be used without accepting",
    "the Terms of Use.",
    "",
    "These terms exist to keep everyone safe. Please never use",
    "NETWATCH - or any similar tool - to spy on other people or",
    "for any illegal or harmful purpose.",
    "",
    "If you change your mind, simply start NETWATCH again and",
    "type 'yes' to accept.",
    "",
    "Thank you for understanding. Stay safe!",
)

WELCOME_BACK = (
    "Welcome back! Last time you chose not to accept the",
    "Terms of Use.",
    "",
    "Before we continue, please tell us honestly why you are",
    "here. There is no wrong answer.",
)

ONLY_TO_GET_IN = (
    "Thank you for being honest - we appreciate it.",
    "",
    "Accepting the Terms of Use is not just a click to get in.",
    "It is a promise that you will use NETWATCH only lawfully",
    "and never to spy on others or cause harm.",
    "",
    "Please read the terms again, and only type 'yes' if you",
    "truly agree with them. If you don't, that's okay -",
    "just type 'no' and NETWATCH will close.",
)


def _lines(lines):
    for line in lines:
        color = C if line.startswith("Thank you") else G
        print(f"      {color}{line}{X}")


def welcome_back():
    while True:
        ui.title("Welcome Back")
        _lines(WELCOME_BACK)
        print()
        ui.opt(1, "I changed my mind - I agree to use NETWATCH responsibly")
        ui.opt(2, "I'm only back because NETWATCH wouldn't let me in")
        ui.opt(0, "Exit")
        print()
        c = ui.choose()
        if c == "1":
            logger.info("Returning user: changed their mind about the terms")
            return True
        if c == "2":
            logger.info("Returning user: came back only to get in - terms explained again")
            ui.title("A Quick Word")
            _lines(ONLY_TO_GET_IN)
            ui.pause("Press Enter to read the terms...")
            return True
        if c == "0":
            return False


def accept_terms(cfg):
    if cfg["terms_accepted"] == TERMS_VERSION:
        return True
    if cfg["terms_declined"] and not welcome_back():
        return False
    while True:
        ui.title("Terms of Use")
        for line in TERMS:
            print(f"      {G if not line.startswith('  ') else W}{line}{X}")
        print()
        print(f"      {GR}Full text: app/DISCLAIMER.md  ·  License: see LICENSE{X}")
        ui.sep()
        answer = ui.choose("Type 'yes' to accept, 'no' to exit")
        if answer == ui.REDRAW:
            continue
        if answer.lower() in ("yes", "y"):
            cfg["terms_accepted"] = TERMS_VERSION
            cfg["terms_declined"] = False
            logger.info(f"Terms of use accepted (version {TERMS_VERSION})")
            return True
        if answer.lower() in ("no", "n"):
            cfg["terms_declined"] = True
            logger.info("Terms of use declined - exiting")
            ui.title("Terms Not Accepted")
            _lines(DECLINED)
            print()
            ui.pause("Press Enter to exit...")
            return False


def setup_folder_icon():
    try:
        if winshell.apply_folder_icon():
            logger.info("NETWATCH folder icon applied")
    except OSError as ex:
        logger.warn(f"Could not apply folder icon: {ex}")


def toggle_shortcut():
    try:
        if winshell.shortcut_exists():
            winshell.remove_shortcut()
            logger.info("Desktop shortcut removed")
            ui.ok("Desktop shortcut removed.")
        else:
            winshell.create_shortcut()
            logger.info("Desktop shortcut created")
            ui.ok("Desktop shortcut created with the NETWATCH icon.")
    except OSError as ex:
        logger.error(f"Desktop shortcut failed: {ex}")
        ui.err(f"Could not change the desktop shortcut: {ex}")


MODIFIED = (
    "This copy of NETWATCH has been changed since it was released.",
    "",
    "That is fine for your own use - the license lets you change",
    "NETWATCH for yourself. But you may NOT:",
    "",
    "  - publish, share or upload this changed version anywhere,",
    "  - give it to other people, or sell it,",
    "  - present it (or the original) as your own work.",
    "",
    "The original NETWATCH is made by KØRVEX:",
    "  https://github.com/K0RVEXx/NETWATCH",
)


def integrity_notice(cfg):
    """Remind the user what the license allows if program files were changed.
    Shown once per changed state; never blocks."""
    try:
        result = integrity.check()
    except OSError as ex:
        logger.warn(f"Integrity check failed: {ex}")
        return
    if result["status"] != "modified":
        return
    files = result["changed"] + result["missing"] + result["added"]
    logger.warn(f"Modified copy detected ({len(files)} file(s) differ from the release)")
    if cfg["integrity_ack"] == result["fingerprint"]:
        return
    while True:
        ui.title("Modified Copy")
        for line in MODIFIED:
            color = W if line.startswith("  -") else C if "github.com" in line else G
            print(f"      {color}{line}{X}")
        print()
        print(f"      {GR}Changed files: {', '.join(files[:4])}{' …' if len(files) > 4 else ''}{X}")
        ui.sep()
        ui.opt(1, "I understand - don't show this again for these changes")
        ui.opt(0, "Continue")
        c = ui.choose()
        if c == ui.REDRAW:
            continue
        if c == "1":
            cfg["integrity_ack"] = result["fingerprint"]
            logger.info("Modified-copy notice acknowledged")
        return


def offer_shortcut(cfg):
    """Ask once, after the terms are accepted, whether to create a desktop shortcut."""
    if cfg["shortcut_asked"] or not winshell.SUPPORTED or winshell.shortcut_exists():
        return
    ui.title("Desktop Shortcut")
    for line in (
        "Would you like a NETWATCH shortcut on your desktop?",
        "",
        "It starts NETWATCH with one double-click and shows the",
        "NETWATCH icon. You can add or remove it any time in",
        "Settings -> [D] Desktop shortcut.",
    ):
        print(f"      {G}{line}{X}")
    print()
    answer = ui.ask("Create desktop shortcut? (y/n)", "y").lower()
    cfg["shortcut_asked"] = True
    if answer.startswith("y"):
        toggle_shortcut()
        time.sleep(1.5)


def main():
    ui.init()
    logger.info(f"NETWATCH {VERSION} started")
    setup_folder_icon()
    app = App()
    if app.cfg["start_maximized"]:
        ui.maximize_window()
    atexit.register(app.shutdown)
    try:
        if accept_terms(app.cfg):
            integrity_notice(app.cfg)
            offer_shortcut(app.cfg)
            app.monitor.start()
            app.main_menu()
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        app.shutdown()
