from pathlib import Path

SEED = 42
START_DATE = "2026-04-01"
END_DATE = "2026-09-30"          # ~6 місяців

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

MAX_TEST_ATTEMPTS = 3