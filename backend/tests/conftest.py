import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend" / "src"))

# Keep tests off DynamoDB and out of the developer's working database.
os.environ["AAHAR_STORAGE"] = "local"
os.environ.pop("PROFILES_TABLE", None)
os.environ["AAHAR_LOCAL_DB"] = str(Path(__file__).parent / ".pytest-db.json")


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db():
    db = Path(os.environ["AAHAR_LOCAL_DB"])
    db.unlink(missing_ok=True)
    yield
    db.unlink(missing_ok=True)
