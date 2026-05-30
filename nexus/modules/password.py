"""Password Fortress: entropy analysis, breach checking, and generation.

Breach checks use the Have I Been Pwned range API with k-anonymity — only
the first five characters of the SHA-1 hash ever leave the machine, so the
password itself is never transmitted.
"""

from __future__ import annotations

import hashlib
import math
import re
import secrets
import string

import requests
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from ..config import get
from ..theme import BOX_TABLE, C_ACC, C_CRIT, C_PRI, C_WARN
from ..ui import console, header

# A compact wordlist for passphrase generation (kept inline so the package
# stays self-contained with no external data files).
_WORDS = (
    "able acid aged also area army away baby back ball band bank base bath bear "
    "beat been beer bell belt best bird blow blue boat body bone book boom boot "
    "born boss both bowl bulk burn bush busy cake call calm came camp card care "
    "case cash cast cell chat chip city clay clip club coal coat code cold come "
    "cook cool cope copy core corn cost crew crop dark data date dawn days dead "
    "deal dean dear debt deep deer desk dial dirt dish dock done door dose down "
    "drag draw drew drop drug drum dual duke dust duty each earn ease east easy "
    "edge else even ever evil exit face fact fade fail fair fall fame farm fast "
    "fate fear feed feel feet fell felt file fill film find fine fire firm fish "
    "five flag flat flow food fool foot ford form fort four free frog fuel full "
    "fund gain game gate gave gear gene gift girl give glad goal goat goes gold "
    "golf gone good gray grew grey grid grim grin grip grow gulf hair half hall "
    "hand hang hard harm hate have hawk head heal heap hear heat held hell helm "
    "help herb herd here hero hide high hill hint hire hold hole holy home hope "
    "horn hour huge hull hunt hurt icon idea idle inch into iron item jack jail "
    "jane jazz jean join joke jump june junk jury just keen keep kept kick kind "
    "king kiss kite knee knew knot know lack lady laid lake lamb lamp land lane "
    "last late lazy lead leaf lean leap left lend lens less life lift like limb "
    "lime line link lion list live load loan lock loft logo lone long look loop "
    "lord lose loss lost loud love luck lump lung made mail main make male mall "
    "many maps mare mark mars mask mass mate math maze mead meal mean meat meet "
    "melt menu mere mesh mile milk mill mind mine mint miss mist mode mole monk "
    "mood moon more moss most moth move much mule muse must mute myth nail name "
    "navy near neat neck need news next nice nick node none noon norm nose note "
    "noun oath obey odds okay once only onto open oral oval oven over pace pack "
    "page paid pain pair pale palm park part pass past path peak peer perk pest "
    "pick pile pill pine pink pint pipe plan play plot plug plus poem poet pole "
    "poll pond pool poor pope pork port pose post pour pray prey prop pull pump "
    "pure push quit race rack rage rail rain rake ramp rank rare rate read real "
    "rear rely rent rest rice rich ride ring riot rise risk road roar robe rock "
    "role roll roof room root rope rose ruby rude ruin rule rush rust safe sage "
    "said sail sake sale salt same sand save scan seal seam seat seed seek seem "
    "seen self sell semi send sent ship shop shot show shut sick side sign silk "
    "sing sink site size skin skip slab slam slid slim slip slot slow snap snow "
    "soap soar sock soda sofa soft soil sold sole solo some song soon sort soul "
    "soup sour spin spot spun star stay stem step stir stop stub such suit sung "
    "sunk sure surf swam swap sway tail take tale talk tall tank tape task team "
    "tear tech tell tend tent term test text than that them then they thin this "
    "thus tide tied tier ties tile till tilt time tiny tire toad told toll tone "
    "tool tops torn tour town trap tray tree trim trip true tube tune turn twin "
    "type unit upon urge used user vary vast verb very vest vice view vine void "
    "vote wage wait wake walk wall wand want ward ware warm warn wash wave weak "
    "wear weed week well went were west what when whip whom wide wife wild will "
    "wind wine wing wipe wire wise wish wolf wood wool word wore work worm worn "
    "wrap yard yarn year yoga zero zone zoom"
).split()


def entropy(pwd: str) -> float:
    """Estimate password entropy in bits from the character pool used."""
    pool = 0
    if re.search(r"[a-z]", pwd):
        pool += 26
    if re.search(r"[A-Z]", pwd):
        pool += 26
    if re.search(r"\d", pwd):
        pool += 10
    if re.search(r"[^a-zA-Z0-9]", pwd):
        pool += 32
    return len(pwd) * math.log2(pool) if pool else 0.0


def crack_time(bits: float, guesses_per_sec: float = 1e10) -> str:
    """Human-readable estimated offline crack time for the given entropy.

    Assumes ~10 billion guesses/sec (a high-end GPU rig on fast hashes).
    """
    seconds = (2 ** bits) / 2 / guesses_per_sec
    units = [
        ("centuries", 60 * 60 * 24 * 365 * 100),
        ("years", 60 * 60 * 24 * 365),
        ("days", 60 * 60 * 24),
        ("hours", 60 * 60),
        ("minutes", 60),
        ("seconds", 1),
    ]
    if seconds < 1:
        return "instantly"
    for name, size in units:
        if seconds >= size:
            value = seconds / size
            if value > 1e6:
                return f"{value:.1e} {name}"
            return f"{value:,.1f} {name}"
    return "instantly"


def strength_label(bits: float) -> tuple[str, str]:
    """Map entropy to a (label, colour) pair."""
    if bits < 40:
        return "WEAK", C_CRIT
    if bits < 60:
        return "FAIR", C_WARN
    if bits < 80:
        return "STRONG", C_ACC
    return "VERY STRONG", f"bold {C_ACC}"


def hibp_check(pwd: str) -> tuple[bool | None, int]:
    """Check a password against HIBP. Returns (pwned, times). None = offline."""
    sha = hashlib.sha1(pwd.encode()).hexdigest().upper()
    try:
        r = requests.get(
            f"https://api.pwnedpasswords.com/range/{sha[:5]}",
            timeout=6,
            headers={"Add-Padding": "true"},
        )
        for line in r.text.splitlines():
            suffix, count = line.split(":")
            if suffix == sha[5:]:
                return True, int(count)
        return False, 0
    except Exception:
        return None, 0


def generate_password(length: int = 20, symbols: bool = True) -> str:
    """Generate a random password guaranteed to span character classes."""
    chars = string.ascii_letters + string.digits
    if symbols:
        chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"
    while True:
        pwd = "".join(secrets.choice(chars) for _ in range(length))
        if (
            re.search(r"[a-z]", pwd)
            and re.search(r"[A-Z]", pwd)
            and re.search(r"\d", pwd)
            and (not symbols or re.search(r"[^a-zA-Z0-9]", pwd))
        ):
            return pwd


def generate_passphrase(words: int = 4, sep: str = "-") -> str:
    """Generate a memorable diceware-style passphrase with a number."""
    chosen = [secrets.choice(_WORDS).capitalize() for _ in range(words)]
    chosen.insert(secrets.randbelow(words + 1), str(secrets.randbelow(100)))
    return sep.join(chosen)


def _analyze(pwd: str) -> None:
    bits = entropy(pwd)
    label, col = strength_label(bits)

    with console.status(f"[{C_PRI}]Checking 14 billion+ breached passwords…"):
        pwned, count = hibp_check(pwd)

    t = Table(box=BOX_TABLE, border_style=C_PRI, show_header=False,
              title=f"[bold {C_PRI}]  PASSWORD ANALYSIS  [/]")
    t.add_column("Field", style=f"bold {C_PRI}", width=20)
    t.add_column("Value")

    t.add_row("Length", str(len(pwd)))
    t.add_row("Entropy", f"{bits:.1f} bits")
    t.add_row("Strength", f"[{col}]{label}[/]")
    t.add_row("Crack time", f"[{col}]~{crack_time(bits)}[/]  [dim](offline, 10B guesses/s)[/]")

    if pwned is None:
        t.add_row("Breach", f"[{C_WARN}]API unavailable (offline?)[/]")
    elif pwned:
        t.add_row("Breach", f"[bold {C_CRIT}]COMPROMISED — seen {count:,} times in breaches![/]")
    else:
        t.add_row("Breach", f"[bold {C_ACC}]CLEAN — not in any known breach[/]")

    issues = []
    if len(pwd) < 12:
        issues.append("Too short (<12)")
    if not re.search(r"[A-Z]", pwd):
        issues.append("No uppercase")
    if not re.search(r"\d", pwd):
        issues.append("No digits")
    if not re.search(r"[^a-zA-Z0-9]", pwd):
        issues.append("No symbols")
    t.add_row("Issues", f"[{C_WARN}]" + " · ".join(issues) + "[/]" if issues
              else f"[{C_ACC}]None[/]")

    console.print(t)


def _generate_menu() -> None:
    mode = Prompt.ask("Type", choices=["password", "passphrase"], default="password")
    count = IntPrompt.ask("How many?", default=5)

    t = Table(title=f"Generated {mode}s", box=BOX_TABLE, border_style=C_ACC)
    t.add_column("#", style=f"dim {C_PRI}", width=4)
    t.add_column(mode.capitalize(), style=f"bold {C_ACC}")
    t.add_column("Entropy", style=C_WARN, width=10)
    t.add_column("Strength", width=14)

    if mode == "password":
        length = IntPrompt.ask("Length", default=int(get("password_length")))
        symbols = Prompt.ask("Include symbols?", choices=["y", "n"], default="y") == "y"
        for i in range(1, count + 1):
            pwd = generate_password(length, symbols)
            bits = entropy(pwd)
            label, col = strength_label(bits)
            t.add_row(str(i), pwd, f"{bits:.0f} bits", f"[{col}]{label}[/]")
    else:
        nwords = IntPrompt.ask("Words per phrase", default=4)
        for i in range(1, count + 1):
            phrase = generate_passphrase(nwords)
            bits = entropy(phrase)
            label, col = strength_label(bits)
            t.add_row(str(i), phrase, f"{bits:.0f} bits", f"[{col}]{label}[/]")

    console.print(t)


def run() -> None:
    """Password Fortress menu loop."""
    header("PASSWORD FORTRESS")
    while True:
        console.print(f"[bold {C_PRI}]1[/]  Analyze + Breach Check")
        console.print(f"[bold {C_PRI}]2[/]  Generate Passwords / Passphrases")
        console.print(f"[bold {C_PRI}]3[/]  Back\n")
        choice = Prompt.ask(f"[{C_PRI}]>[/]", choices=["1", "2", "3"])

        if choice == "3":
            break
        if choice == "1":
            pwd = Prompt.ask(f"[{C_PRI}]Enter password[/]", password=True)
            if pwd:
                _analyze(pwd)
        elif choice == "2":
            _generate_menu()
        console.print()
