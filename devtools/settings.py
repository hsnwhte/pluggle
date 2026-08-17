import os
from pathlib import Path

from dotenv import load_dotenv

DEV_ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=DEV_ROOT_DIR.parent / ".env")
DEV_DB_DIR = DEV_ROOT_DIR / "databases"
DEV_DB_DIR.mkdir(parents=True, exist_ok=True)


DEV_RUNTIME_SQLITE = f"sqlite:///{DEV_ROOT_DIR / 'databases' / 'dev_runtime.sqlite'}"
DEV_RUNTIME_POSTGRE = "postgresql://postgres:testpass@localhost:5432/postgres"

REAL_RUNTIME_STORE = os.environ.get("PLUGGLE_STORE_ADDRESS")


DEV_SOURCE_API_URL = "https://jsonplaceholder.typicode.com/comments/1"
DEV_SOURCE_DB_URL = f"sqlite:///{DEV_DB_DIR / 'dev_source.sqlite'}"
DEV_SOURCE_FILE_DIR = DEV_ROOT_DIR / "test_data" / "input"
DEV_TARGET_API_URL = "https://jsonplaceholder.typicode.com/posts/1"
DEV_TARGET_DB_URL = f"sqlite:///{DEV_DB_DIR / 'dev_target.sqlite'}"
DEV_TARGET_FILE_DIR = DEV_ROOT_DIR / "test_data" / "output"
