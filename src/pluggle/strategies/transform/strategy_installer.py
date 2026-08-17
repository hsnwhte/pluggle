import importlib.util
import shutil
import tempfile
from pathlib import Path

import httpx

from pluggle.exceptions import errors
from pluggle.strategies.protocols import TransformStrategyProtocol

CATALOG_URL = (
    "https://raw.githubusercontent.com/hsnwhte/pluggle-strategies/main/catalog.json"
)
RAW_BASE = "https://raw.githubusercontent.com/hsnwhte/pluggle-strategies/main/"

INSTALLED_DIR = Path(__file__).resolve().parent / "installed"
INSTALLED_DIR.mkdir(exist_ok=True)


def install_strategy(
    *, strategy_path: Path | None = None, repo_name: str | None = None
) -> tuple[str, str | None]:
    doc_url = None
    if not strategy_path and not repo_name:
        raise errors.StrategySetupError(
            "No argument is provided. Expected: 'strategy_path' OR 'repo_name'"
        )
    if repo_name is not None:
        strategy_path, doc_url = _fetch_strategy_from_repo(repo_name=repo_name)

    strategy = _load_strategy_from_file(file_path=strategy_path)
    strategy_name = strategy.meta.name + "_" + strategy.meta.version

    destination = INSTALLED_DIR / f"{strategy_name}.py"
    shutil.copy(strategy_path, destination)

    return strategy_name, doc_url


def uninstall_strategy(*, strategy_name: str) -> None:
    target = INSTALLED_DIR / f"{strategy_name}.py"
    if not target.exists():
        raise errors.StrategyNotFoundError(
            f"No installed strategy with name '{strategy_name}'."
        )

    target.unlink()


def uninstall_all() -> None:
    print(INSTALLED_DIR)
    names = [f.stem for f in INSTALLED_DIR.glob("*.py")]
    print(names)
    if not names:
        raise errors.StrategyNotFoundError("No installed strategies to remove.")
    for name in names:
        uninstall_strategy(strategy_name=name)


def _fetch_strategy_from_repo(*, repo_name: str) -> tuple[Path, str | None]:
    try:
        catalog_response = httpx.get(CATALOG_URL, timeout=10.0)
        catalog_response.raise_for_status()
    except httpx.HTTPError as e:
        raise errors.StrategyNotFoundError(
            f"Could not reach the strategy catalog: {e}"
        ) from e

    catalog = catalog_response.json()
    entry = catalog.get("strategies", {}).get(repo_name)
    if entry is None:
        raise errors.StrategyNotFoundError(
            f"No strategy named '{repo_name}' found in the catalog"
        )

    file_url = RAW_BASE + entry["file"]
    try:
        file_response = httpx.get(file_url, timeout=10.0)
        file_response.raise_for_status()
    except httpx.HTTPError as e:
        raise errors.StrategyNotFoundError(
            f"Could not download strategy file: {e}"
        ) from e

    temp_path = Path(tempfile.gettempdir()) / f"{repo_name}.py"
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
    if not hasattr(strategy_class, "transform") + hasattr(strategy_class, "meta"):
        raise errors.StrategyNotFoundError(
            f"{strategy_class.__class__.__name__} does not implement "
            f"TransformStrategyProtocol"
        )
    return strategy_class
