import os
from pathlib import Path

from dotenv import load_dotenv

from pluggle.enums import ContentFormat

### --- SYSTEM ADDRESSES
# ----- Project Root
RUNTIME_ROOT = Path.cwd()

# ----- Environment
load_dotenv()

# ----- Pipeline Store
DEFAULT_RUNTIME_STORE_PATH = RUNTIME_ROOT / "data" / "runtime.sqlite"
DEFAULT_RUNTIME_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
RUNTIME_STORE = os.environ.get(
    "PLUGGLE_STORE_ADDRESS", f"sqlite:///{DEFAULT_RUNTIME_STORE_PATH}"
)

# ----- Log Output
LOG_DIR = Path(os.environ.get("LOG_DIR", RUNTIME_ROOT / "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

# --- Installed Strategies
INSTALLED_STRATEGIES_DIR = Path(
    os.environ.get("PLUGGLE_STRATEGIES_DIR", RUNTIME_ROOT / "data" / "strategies")
)
INSTALLED_STRATEGIES_DIR.mkdir(parents=True, exist_ok=True)

# --- System variables
NORMALIZED_FORMAT = ContentFormat.JSON
