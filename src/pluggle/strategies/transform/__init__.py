from pluggle.settings import INSTALLED_STRATEGIES_DIR
from pluggle.strategies.protocols import TransformStrategyProtocol
from pluggle.strategies.transform.default import TransformStrategySamplePassthrough
from pluggle.strategies.transform.strategy_manager import _load_strategy_from_file


def _map_key(strategy: type[TransformStrategyProtocol]) -> str:
    return f"{strategy.meta.name}_{strategy.meta.version}"


TRANSFORM_STRATEGY_MAP: dict[str, type[TransformStrategyProtocol]] = {
    _map_key(TransformStrategySamplePassthrough): TransformStrategySamplePassthrough,
}


for file_path in sorted(INSTALLED_STRATEGIES_DIR.glob("*.py")):
    strategy = _load_strategy_from_file(file_path=file_path)
    TRANSFORM_STRATEGY_MAP[_map_key(strategy)] = strategy
