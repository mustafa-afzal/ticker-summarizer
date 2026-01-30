import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = BASE_DIR / "cache"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
DB_PATH = BASE_DIR / "pitchsheet.db"

CACHE_DIR.mkdir(exist_ok=True)
ARTIFACTS_DIR.mkdir(exist_ok=True)

SEC_USER_AGENT = "PitchSheetAgent (mafz@umich.edu)"
SEC_BASE_URL = "https://data.sec.gov"
SEC_RATE_LIMIT_DELAY = 0.15  # seconds between requests (SEC asks for max 10/sec)

MAPPING_VERSION = "1.0.0"
