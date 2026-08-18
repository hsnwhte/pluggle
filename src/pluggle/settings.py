import os
from pathlib import Path

from dotenv import load_dotenv

from pluggle.enums import ContentFormat

### --- SYSTEM ADDRESSES
# ----- Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ----- Environment
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# ----- Pipeline Store
DEFAULT_RUNTIME_STORE_PATH = PROJECT_ROOT / "data" / "runtime.sqlite"
DEFAULT_RUNTIME_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
RUNTIME_STORE = os.environ.get(
    "PLUGGLE_STORE_ADDRESS", f"sqlite:///{DEFAULT_RUNTIME_STORE_PATH}"
)

# ----- Log Output
LOG_DIR = Path(os.environ.get("LOG_DIR", PROJECT_ROOT / "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

# --- Installed Strategies
INSTALLED_STRATEGIES_DIR = Path(
    os.environ.get("PLUGGLE_STRATEGIES_DIR", PROJECT_ROOT / "data" / "strategies")
)
INSTALLED_STRATEGIES_DIR.mkdir(parents=True, exist_ok=True)

# --- System variables
NORMALIZED_FORMAT = ContentFormat.JSON
