from pathlib import Path

from pluggle.enums import ContentFormat, PluggleIOType
from pluggle.exceptions import errors
from pluggle.strategies import decode, export, extract, fetch, load, transform
from pluggle.strategies.protocols import (
    DecodeStrategyProtocol,
    ExportStrategyProtocol,
    ExtractStrategyProtocol,
    FetchStrategyProtocol,
    LoadStrategyProtocol,
    TransformStrategyProtocol,
)


class Selector:
    """Resolves which strategy class handles a given phase.

    The single dispatch point between the Orchestrator and the strategy
    maps, so adding a format or IO type means registering a class rather
    than touching pipeline code.
    """
    @staticmethod
    def get_fetch_strategy(source_type: PluggleIOType) -> FetchStrategyProtocol:
        smap = fetch.FETCH_STRATEGY_MAP
        try:
            return smap[source_type.value]
        except KeyError as e:
            raise errors.StrategyNotFoundError(
                f"No fetch strategy for '{source_type.value}' could be found."
            ) from e

    @staticmethod
    def get_decode_strategy(source_address: Path) -> DecodeStrategyProtocol:
        file_ext = source_address.suffix.lstrip(".")
        smap = decode.DECODE_STRATEGY_MAP
        try:
            return smap[file_ext]
        except KeyError as e:
            raise errors.StrategyNotFoundError(
                f"No decode strategy for '{file_ext}' could be found."
            ) from e

    @staticmethod
    def get_extract_strategy(source_format: ContentFormat) -> ExtractStrategyProtocol:
        smap = extract.EXTRACT_STRATEGY_MAP
        try:
            return smap[source_format.value]
        except KeyError as e:
            raise errors.StrategyNotFoundError(
                f"No extract strategy for '{source_format.value}' could be found."
            ) from e

    @staticmethod
    def get_transform_strategy(strategy_uid: str) -> type[TransformStrategyProtocol]:
        smap = transform.TRANSFORM_STRATEGY_MAP
        try:
            return smap[strategy_uid]
        except KeyError as e:
            raise errors.StrategyNotFoundError(
                f"No transform strategy with uid '{strategy_uid}' could be found."
            ) from e

    @staticmethod
    def get_load_strategy(target_type: PluggleIOType) -> LoadStrategyProtocol:
        smap = load.LOAD_STRATEGY_MAP
        try:
            return smap[target_type.value]
        except KeyError as e:
            raise errors.StrategyNotFoundError(
                f"No load strategy for '{target_type.value}' could be found."
            ) from e

    @staticmethod
    def get_export_strategy() -> ExportStrategyProtocol:
        """Return the export strategy.

        Takes no argument: export always writes to a file, and the
        strategy is format-agnostic.
        """
        smap = export.EXPORT_STRATEGY_MAP
        try:
            return smap["file"]
        except KeyError as e:
            raise errors.StrategyNotFoundError(
                "No export strategy could be found."
            ) from e


selector = Selector()
