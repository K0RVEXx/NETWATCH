# Security Policy

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Report them privately through GitHub:
**Security → Report a vulnerability** on this repository
(GitHub private vulnerability reporting).

Include a description, steps to reproduce and the affected version.
Please allow reasonable time for a fix before any public disclosure.

## Scope

Examples of relevant issues:

- The dashboard being reachable from other machines (it must listen on `127.0.0.1` only)
- The dashboard accepting changes or requests from other websites (it must stay read-only)
- Data from remote hosts (e.g. host names) being rendered as HTML in the dashboard
- Personal data being sent anywhere other than the documented location lookup

See [DISCLAIMER.md](app/DISCLAIMER.md) for what NETWATCH does and does not send.
