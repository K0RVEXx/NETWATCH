# Contributing to NETWATCH

Thank you for your interest in improving NETWATCH!

## Reporting bugs

Open an issue and include:

- Windows version, Python version (`python --version`) and terminal (cmd / Windows Terminal)
- Steps to reproduce, what you expected and what happened
- Relevant lines from `app/logs/netwatch.log`

**Remove IP addresses, host names and any personal data before posting.**

## Suggesting features

Open an issue describing the problem the feature solves, how it would work from the
user's point of view (which menu, which setting, what the dashboard shows), and any
alternatives you considered.

## Pull requests

1. Fork the repository and create a branch from `main` (e.g. `fix/geo-cache`).
2. Keep each pull request focused on one change.
3. Update `README.md` and `app/CHANGELOG.md` when behavior or settings change.
4. Describe what you changed and how you tested it.

## Code quality

- Python 3.8+ compatible, standard library first; new dependencies need a good reason
  and must be added to `app/requirements.txt`.
- Keep the modular structure: UI in `ui.py` / `app.py`, scanning in `monitor.py`,
  rules in `alerts.py`, lookups in `geo.py`, web server in `dashboard.py`.
- All user-facing text (menus, statuses, errors, logs, dashboard) is in **English**.
- NETWATCH monitors **only the computer it runs on**. Features that observe other people's
  devices or traffic will not be accepted.
- The dashboard must listen on `127.0.0.1` only, stay read-only, and render remote data
  (host names, organisations) as text, never as HTML.
- Never send data anywhere except the documented location lookup; document any change.
- No fake or simulated results. No administrator rights may be required.

## Testing before submitting

After changing program files, refresh the file list used by the modified-copy check:

```bash
python tools/update_integrity.py
```

Then run the automated tests:

```bash
python -m pytest tests
```

Then check manually on Windows:

1. `NETWATCH.bat` starts, and every main menu item opens and returns.
2. **Live Connections** lists programs, hosts and countries and updates every second.
3. A new program going online raises an alert after learning mode; approving it works.
4. **Open Dashboard** shows the map, table and alerts at `http://127.0.0.1:8765/`.
5. With **Location lookup** turned off, no requests are sent to ip-api.com.
6. Exit with `[0]`, with Ctrl+C and by closing the window — the dashboard port is released.
7. Resize the window / toggle full screen and confirm the layout redraws correctly.

## License of contributions

By submitting a contribution, you agree that KØRVEX may use, change and release it as
part of NETWATCH under the project's license (see [LICENSE](../LICENSE)). Forking this
repository on GitHub to prepare a pull request is fine; publishing a fork as a separate
project is not allowed.
