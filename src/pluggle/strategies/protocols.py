from pathlib import Path
from typing import Protocol, runtime_checkable

from pluggle.enums import ContentFormat
from pluggle.models.dto import (
    ExtractableData,
    StrategyMeta,
    TransformableData,
    TransformedData,
)


class FetchStrategyProtocol(Protocol):
    @staticmethod
    def fetch(*, address: str, table_name: str | None = None) -> ExtractableData: ...


class DecodeStrategyProtocol(Protocol):
    @staticmethod
    def decode(*, file_path: Path) -> ExtractableData: ...


class ExtractStrategyProtocol(Protocol):
    @staticmethod
    def extract(*, content: bytes) -> TransformableData: ...


@runtime_checkable
class TransformStrategyProtocol(Protocol):
    meta: StrategyMeta

    def transform(self) -> TransformedData: ...


class LoadStrategyProtocol(Protocol):
    @staticmethod
    def load(
        *,
        data: TransformedData,
        address: str,
        target_format: ContentFormat,
        table_name: str | None = None,
    ) -> None: ...


class ExportStrategyProtocol(Protocol):
    @staticmethod
    def export(*, data: TransformedData, file_path: Path) -> None: ...
