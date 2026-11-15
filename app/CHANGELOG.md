# Changelog

All notable changes to NETWATCH are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-11-15

### Added
- Live list of programs connecting to the internet with remote host, port, country, city
  and network owner (psutil, no administrator rights)
- Alerts: new app online, known app in a new country, suspicious ports, programs running
  from unusual folders
- Learning mode on first start and approval of known behaviour
- Location lookup (ip-api.com batch API) and reverse DNS with on-disk cache
- Local read-only web dashboard with world map, live table, top apps and countries,
  upload and download speed
- Terminal UI in the KØRVEX style, terms of use on first start, auto-saved settings,
  activity log
- NETWATCH icon on the folder and an optional desktop shortcut with the icon
- "Made by KØRVEX" in About, dashboard and README
- Automated tests and GitHub Actions CI on Windows
- Open source documentation: MIT License, README, BRANDING, DISCLAIMER, CONTRIBUTING, SECURITY
