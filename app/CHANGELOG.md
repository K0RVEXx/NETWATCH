# Changelog

All notable changes to NETWATCH are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).


## [Unreleased]

### Added
- Modified-copy check: NETWATCH compares its program files with the released list on start
  and, if they were changed, reminds the user what the license allows (shown once per change,
  never blocks)

### Changed
- License: from now on **PolyForm Internal Use License 1.0.0** with an extra permission
  for personal use - you may use and change the software for yourself, but not publish,
  share or redistribute it. Versions up to v1.0.1 remain under the MIT License

## [1.0.1] - 2026-11-15

### Changed
- Redesigned dashboard in a clean security-tool style: NETWATCH icon in the title bar,
  status strip, live traffic chart with axes (last 2 minutes), connections table with
  search, "only flagged" filter and sortable columns, alerts list, destination map and
  breakdowns by app and country

### Fixed
- The destination map now always frames every destination and draws the full base map

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
