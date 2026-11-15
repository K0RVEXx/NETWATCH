"""NETWATCH - Network Traffic Monitor (KØRVEX)."""
import os

VERSION = "1.0.0"
TERMS_VERSION = "1"   # bump when the terms of use change -> users are asked again
NAME = "NETWATCH"
SLOGAN = "Bláthy On Top"     # shown under the name - Bláthy is the author's school
SCHOOL = "Bláthy"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # NETWATCH/app
ROOT_DIR = os.path.dirname(BASE_DIR)                                       # NETWATCH
WEB_DIR = os.path.join(BASE_DIR, "web")
