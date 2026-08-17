from pathlib import Path

from pluggle.strategies.protocols import TransformStrategyProtocol
from pluggle.strategies.transform.default import TransformStrategySamplePassthrough
from pluggle.strategies.transform.strategy_installer import _load_strategy_from_file

TRANSFORM_STRATEGY_MAP: dict[str, type[TransformStrategyProtocol]] = {
    "default_v1.0": TransformStrategySamplePassthrough,  # constant, not to be erased
}

INSTALLED_DIR = Path(__file__).resolve().parent / "installed"
INSTALLED_DIR.mkdir(exist_ok=True)

for file_path in sorted(INSTALLED_DIR.glob("*.py")):
    TRANSFORM_STRATEGY_MAP[file_path.stem] = _load_strategy_from_file(
        file_path=file_path
    )
