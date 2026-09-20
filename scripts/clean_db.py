"""Drop test rows from the local demo database.

`backend/.local-db.json` is the dev store, and it accumulates whatever the test
scripts scanned — barcodes like `t1`/`t2` ("Test Sauce", "Plain Water") that
only exist in fixtures. Those rows then show up in "Recent scans" on the home
screen and in the Compare picker, where choosing one fails outright because no
lookup can resolve the barcode.

Run from the repo root:

    .venv/bin/python scripts/clean_db.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "backend" / ".local-db.json"

# A real barcode is 8-14 digits; `photo_*` is a label photo the app can
# re-evaluate from its stored product. Anything else came from a fixture.
REAL_BARCODE = re.compile(r"^\d{8,14}$")


def is_test_row(barcode: str) -> bool:
    return not (REAL_BARCODE.match(barcode) or barcode.startswith("photo_"))


def main() -> None:
    if not DB.is_file():
        print(f"{DB} does not exist yet — nothing to clean.")
        return

    db = json.loads(DB.read_text())

    profiles = db.get("profiles", [])
    kept_profiles = [p for p in profiles if not str(p.get("name", "")).startswith("Test")]

    history = db.get("history", [])
    dropped = [h for h in history if is_test_row(str(h.get("barcode", "")))]
    kept_history = [h for h in history if not is_test_row(str(h.get("barcode", "")))]

    db["profiles"] = kept_profiles
    db["history"] = kept_history
    DB.write_text(json.dumps(db, indent=2))

    for row in dropped:
        print(f"  dropped scan {row.get('barcode')!r}")
    print(
        f"Cleaned {DB.name}: "
        f"{len(profiles) - len(kept_profiles)} profile(s), {len(dropped)} scan(s) removed."
    )


if __name__ == "__main__":
    main()
