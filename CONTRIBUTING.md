# Contributing to NEXUS

Thanks for your interest in improving NEXUS! Contributions of all kinds are
welcome — bug reports, feature ideas, documentation, and code.

## Getting set up

```bash
git clone https://github.com/shaheerch/nexus.git
cd nexus
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Unix:     source .venv/bin/activate
pip install -e .
```

Run the tool with `python -m nexus`.

## Project layout

```
nexus/
├── __main__.py      # menu + CLI dispatch
├── ui.py            # shared console, banner, helpers
├── theme.py         # colours and box styles
├── config.py        # user settings
├── paths.py         # user data locations
└── modules/         # one file per feature, each exposing run()
```

To add a feature, create `nexus/modules/<name>.py` exposing a `run()`
function, then register it in the `MODULES` list in `nexus/__main__.py`.

## Code style

- Target Python 3.9+ and keep modules cross-platform where practical.
- Follow [PEP 8](https://peps.python.org/pep-0008/); lines ≤ 100 chars.
- Add docstrings to public functions and a module-level docstring to each file.
- Prefer the shared `console` from `nexus.ui` over `print`.
- Keep dependencies minimal (`rich`, `requests`, `psutil`).

If you have `ruff` installed: `ruff check nexus`.

## Responsible use

NEXUS includes active network tooling (host discovery, port scanning). Only
run these against systems you own or are explicitly authorised to test. Pull
requests that add aggressive or abuse-oriented capabilities will not be merged.

## Submitting changes

1. Fork and create a feature branch.
2. Make your change with clear, focused commits.
3. Test that `python -m nexus` runs and your module works end-to-end.
4. Open a pull request describing what and why.
