<div align="center">

```
 ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
 ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
 ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
 ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
 ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
 ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
```

# NEXUS

### Cyber Intelligence & Productivity Terminal

**One polished terminal app that fuses practical security tooling with the productivity tools you actually use every day.**

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Built with Rich](https://img.shields.io/badge/built%20with-rich-ff69b4.svg)](https://github.com/Textualize/rich)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## Why NEXUS?

Most people juggle a dozen scattered utilities: a password checker in the browser,
a port scanner from one vendor, a to-do app, a Pomodoro tab, an IP-lookup site.
**NEXUS brings eight of them into a single, fast, keyboard-driven terminal** with a
consistent interface and zero accounts or API keys required for core features.

It is built to be **genuinely useful day-to-day** *and* to **showcase real
engineering** — clean modular architecture, graceful error handling,
cross-platform support, and a privacy-respecting design.

---

## ✨ Features

| # | Module | What it does |
|---|--------|-------------|
| 1 | **System Dashboard** | Live, self-refreshing view of CPU, RAM, disk, **network throughput**, uptime, and the **top processes by CPU**, with a quick security-posture score. |
| 2 | **Password Fortress** | Entropy scoring, **estimated crack time**, and a breach check against **14 billion+ leaked passwords** via Have I Been Pwned — using k-anonymity so your password never leaves your machine. Generates strong passwords *and* memorable passphrases. |
| 3 | **Network Scout** | Multi-threaded LAN **host discovery** with hostname + **MAC address** resolution, and a **TCP port scanner** with per-port risk ratings. Export results to JSON. |
| 4 | **IP / Domain OSINT** | Resolve any IP/domain, then enrich it with **geolocation, ISP, AS, reverse DNS**, and **proxy / VPN / datacenter detection**. One-key "look up *my* public IP." |
| 5 | **Hash & File Integrity** | MD5 / SHA-1 / SHA-256 / SHA-512 of files or text, **verify a download against a checksum**, and **compare two files** byte-for-byte. |
| 6 | **Security Audit** | Read-only local posture check — admin rights, firewall, **Defender + real-time protection**, **RDP**, **SMBv1**, risky open ports, suspicious processes — scored out of 100 with optional JSON report. |
| 7 | **Task Nexus** | A persistent priority to-do list with **due dates**, overdue highlighting, and smart sorting. |
| 8 | **Pomodoro Timer** | Configurable focus/break cycles with a live progress bar, a completion **chime**, and a **session log** of your focus minutes. |

> **Privacy first:** passwords are checked with k-anonymity (only the first 5 chars
> of a SHA-1 hash are sent). All your data — tasks, reports, logs — stays local
> under `~/.nexus/` and is git-ignored.

---

## 🚀 Quick start

### Option A — run it directly (no install)

```bash
git clone https://github.com/Shaheer-Cybersec/nexus.git
cd nexus
python nexus.py
```

The launcher will offer to install the three small dependencies the first time.

### Option B — install as a command

```bash
git clone https://github.com/Shaheer-Cybersec/nexus.git
cd nexus
pip install .
nexus            # now available anywhere
```

### Option C — run the package

```bash
pip install -r requirements.txt
python -m nexus
```

**Requirements:** Python 3.9+ and [`rich`](https://github.com/Textualize/rich),
[`requests`](https://requests.readthedocs.io/), [`psutil`](https://github.com/giampaolo/psutil).

---

## 🎮 Usage

Launch with no arguments for the interactive menu, or jump straight to a module:

```bash
python -m nexus                 # interactive menu
python -m nexus --dashboard     # live system dashboard
python -m nexus --audit         # run a security audit
python -m nexus --password      # password tools
python -m nexus --network       # network scout
python -m nexus --osint         # IP / domain OSINT
python -m nexus --hash          # hashing / integrity
python -m nexus --tasks         # task manager
python -m nexus --pomodoro      # focus timer
python -m nexus --version
```

---

## 🏗️ Architecture

NEXUS is a clean Python package — each feature is an isolated module exposing a
single `run()` entry point, so it's easy to read, test, and extend.

```
nexus/
├── __init__.py        # version & metadata
├── __main__.py        # menu + CLI dispatch  (python -m nexus)
├── ui.py              # shared Rich console, banner, helpers
├── theme.py           # colour palette & box styles
├── config.py          # user settings  (~/.nexus/config.json)
├── paths.py           # centralised user-data locations
└── modules/
    ├── dashboard.py   # live system metrics
    ├── password.py    # entropy, HIBP, generators
    ├── network.py     # host discovery & port scan
    ├── osint.py       # IP / domain intelligence
    ├── hashtool.py    # file & text integrity
    ├── audit.py       # local security posture
    ├── tasks.py       # priority task manager
    └── pomodoro.py    # focus timer
nexus.py               # thin zero-install launcher
```

**Add your own module** in three steps: drop a `run()` function into
`nexus/modules/yours.py`, import it in `nexus/__main__.py`, and add a row to the
`MODULES` list. That's it.

---

## ⚙️ Configuration

Settings live in `~/.nexus/config.json` and are created with sensible defaults on
first run. Tunables include scan thread count, ping/port timeouts, default
Pomodoro durations, password length, and the Pomodoro sound toggle.

---

## 🔐 Responsible use

Network Scout performs **active** host discovery and port scanning. Only use it on
networks and hosts **you own or are explicitly authorised to test**. Unauthorized
scanning may be illegal in your jurisdiction. NEXUS is provided for education,
self-defense, and authorized testing only — see the [LICENSE](LICENSE).

---

## 🗺️ Roadmap

- [ ] Pomodoro focus-history statistics view
- [ ] Export audit reports to HTML/PDF
- [ ] Optional Shodan / VirusTotal enrichment in OSINT (bring-your-own key)
- [ ] Encrypted local password vault
- [ ] Unit-test suite + coverage badge

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for the dev
setup and guidelines.

## 📄 License

Released under the [MIT License](LICENSE).

<div align="center">

**Built with 🐍 Python and ❤️ for security & productivity.**

*If NEXUS is useful to you, consider giving it a ⭐ on GitHub.*

</div>
