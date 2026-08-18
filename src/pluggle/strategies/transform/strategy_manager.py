import importlib.util
import shutil
import tempfile
from pathlib import Path

import httpx

from pluggle.exceptions import errors
from pluggle.settings import INSTALLED_STRATEGIES_DIR
from pluggle.strategies.protocols import TransformStrategyProtocol

CATALOG_URL = (
    "https://raw.githubusercontent.com/hsnwhte/pluggle-strategies/main/catalog.json"
)
RAW_BASE = "https://raw.githubusercontent.com/hsnwhte/pluggle-strategies/main/"


def install_from_path(*, file_path: Path) -> str:
    strategy = _load_strategy_from_file(file_path=file_path)
    strategy_name = strategy.meta.name + "_" + strategy.meta.version
    destination = INSTALLED_STRATEGIES_DIR / f"{strategy_name}.py"
    if destination.exists():
        raise errors.StrategySetupError(
            f"A strategy with name '{strategy_name}' already exists."
        )
    shutil.copy(file_path, destination)

    return strategy_name


def install_from_repo(*, repo_name: str) -> tuple[str, str]:
    catalog_entries = get_repo_catalog()
    try:
        fetched_strategy_path, doc_url = _fetch_strategy_from_repo(
            catalog_entries=catalog_entries, strategy_name=repo_name
        )
    except errors.StrategyNotFoundError:
        raise
    try:
        strategy_name = install_from_path(file_path=fetched_strategy_path)
        return strategy_name, doc_url
    except errors.StrategySetupError:
        raise


def install_all_in_repo() -> tuple:
    catalog_entries = get_repo_catalog()
    result = []
    total = len(catalog_entries.keys())
    skipped = 0
    for entry in catalog_entries:
        destination = INSTALLED_STRATEGIES_DIR / f"{entry}.py"
        if destination.exists():
            skipped += 1
            continue

        fetched_strategy_path, doc_url = _fetch_strategy_from_repo(
            catalog_entries=catalog_entries, strategy_name=entry
        )
        strategy_name = install_from_path(file_path=fetched_strategy_path)
        result.append((strategy_name, doc_url))
    return total, skipped


def uninstall_strategy(*, strategy_name: str) -> None:
    target = INSTALLED_STRATEGIES_DIR / f"{strategy_name}.py"
    if not target.exists():
        raise errors.StrategyNotFoundError(
            f"No installed strategy with name '{strategy_name}'."
        )
    target.unlink()


def uninstall_all() -> None:
    names = [f.stem for f in INSTALLED_STRATEGIES_DIR.glob("*.py")]
    if not names:
        raise errors.StrategyNotFoundError("No installed strategies to remove.")
    for name in names:
        uninstall_strategy(strategy_name=name)


def get_repo_catalog() -> dict:
    try:
        catalog_response = httpx.get(CATALOG_URL, timeout=10.0)
        catalog_response.raise_for_status()
    except httpx.HTTPError as e:
        raise errors.StrategyNotFoundError(
            f"Could not reach the strategy catalog: {e}"
        ) from e

    catalog = catalog_response.json()
    return catalog.get("strategies", {})


def _fetch_strategy_from_repo(
    *, catalog_entries: dict, strategy_name: str
) -> tuple[Path, str]:
    entry = catalog_entries.get(strategy_name)
    if entry is None:
        raise errors.StrategyNotFoundError(
            f"No strategy named '{strategy_name}' found in the catalog"
        )

    file_url = RAW_BASE + entry["file"]
    try:
        file_response = httpx.get(file_url, timeout=10.0)
        file_response.raise_for_status()
    except httpx.HTTPError as e:
        raise errors.StrategyNotFoundError(
            f"Could not download strategy file: {e}"
        ) from e

    temp_path = Path(tempfile.gettempdir()) / f"{strategy_name}.py"
    temp_path.write_bytes(file_response.content)

    doc_path = entry["file"].rsplit(".", 1)[0] + ".md"
    doc_url = f"https://github.com/hsnwhte/pluggle-strategies/blob/main/{doc_path}"

    return temp_path, doc_url


def _load_strategy_from_file(*, file_path: Path) -> type[TransformStrategyProtocol]:
    try:
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        if spec:
            module = importlib.util.module_from_spec(spec)
        else:
            raise errors.StrategyNotFoundError(
                f"Module spec could not be created for {file_path}."
            )
        if spec.loader:
            spec.loader.exec_module(module)
        else:
            raise errors.StrategyNotFoundError(
                f"Module loader could not be created for {file_path}."
            )
    except (SyntaxError, FileNotFoundError) as e:
        raise errors.StrategyNotFoundError(
            f"Failed to load strategy {file_path}: {e}"
        ) from e

    matches = [name for name in dir(module) if name.startswith("TransformStrategy")]
    if len(matches) == 0:
        raise errors.StrategyNotFoundError(
            f"No class starting with 'TransformStrategy' found in {file_path}"
        )
    if len(matches) > 1:
        raise errors.StrategyNotFoundError(
            f"Multiple classes starting with 'TransformStrategy' found in {file_path}:"
            f" {matches}. Exactly one is required."
        )
    strategy_class = getattr(module, matches[0])
    if not hasattr(strategy_class, "transform") and not hasattr(strategy_class, "meta"):
        raise errors.StrategyNotFoundError(
            f"{strategy_class.__name__} does not implement TransformStrategyProtocol"
        )
    return strategy_class
