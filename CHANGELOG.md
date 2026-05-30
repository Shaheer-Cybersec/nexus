# Changelog

All notable changes to NEXUS are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] — 2026-05-30

### Added
- **Modular package architecture** (`nexus/` with `modules/`) replacing the
  single-file script — each feature is now an isolated, testable module.
- **Hash & File Integrity Toolkit**: MD5/SHA1/SHA256/SHA512 of files and
  text, checksum verification, and two-file comparison.
- **Command-line flags**: `python -m nexus --audit`, `--dashboard`, etc.,
  plus `--version` and `--module`.
- **User config system** at `~/.nexus/config.json` (scan threads, timeouts,
  Pomodoro defaults, sound toggle).
- Dashboard now shows **live network throughput** and a **top-processes**
  panel.
- Password Fortress adds **estimated crack-time** and a **passphrase
  generator**.
- Network Scout adds **MAC address resolution** (ARP), **configurable thread
  counts**, and **JSON report export**.
- OSINT adds a **"look up my public IP"** shortcut.
- Tasks gain **due dates** with overdue highlighting and smart sorting.
- Security Audit adds **Defender, RTP, RDP, and SMBv1 checks** and **JSON
  report export**.
- Pomodoro logs completed sessions and plays a **completion chime**.
- All user data consolidated under `~/.nexus/`.

### Changed
- `nexus.py` is now a thin launcher that bootstraps dependencies and hands
  off to the package.

## [1.0.0] — 2026-05-30

### Added
- Initial single-file release with seven modules: System Dashboard, Password
  Fortress, Network Scout, IP/Domain OSINT, Task Nexus, Security Audit, and
  Pomodoro Timer.
