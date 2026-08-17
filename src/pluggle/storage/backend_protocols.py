from typing import Protocol

from pluggle.enums import ContentFormat, Phase, RunStatus
from pluggle.models.dto import FetchCacheData, PipelineRunRecordData, RegistryRecord


class PipelineRunRecordsProtocol(Protocol):
    def register_run(self) -> int:
        """Persists content, returns an address referencing it."""

    def update_record(
        self,
        *,
        run_id: int,
        status: RunStatus,
        phase: Phase | None = None,
    ) -> int:
        """Updates run status and details if run is interrupted"""
        ...

    def list_runs(self, *, limit: int, offset: int) -> list[PipelineRunRecordData]:
        """Lists previous runs as paginated"""
        ...

    def count_runs(self) -> int: ...


class FetchCacheStoreProtocol(Protocol):
    def save(self, *, api_url: str, registry_address: int, payload_address: str) -> str:
        """Persists fetch cache data to the database"""
        ...

    def load(self, *, api_url: str) -> FetchCacheData:
        """Retreives the fetch cache data"""
        ...


class RegistryStoreProtocol(Protocol):
    def save_entry(
        self,
        *,
        run_id: int,
        phase: Phase,
        content_format: ContentFormat,
        transform_strategy_name: str | None,
        strategy_name: str,
        content_hash: str,
        address: str,
    ) -> int:
        """Persists info from pipeline processors at successive phases."""
        ...

    def get_entry_by_id(self, *, entry_id: int) -> RegistryRecord:
        """Retreives entry object by id"""
        ...

    def get_entry_by_run_id(self, *, run_id: int, phase: Phase) -> RegistryRecord:
        """Retreives entry object by run_id and phase"""
        ...

    def get_entry_by_hash(self, *, content_hash: str) -> RegistryRecord:
        """Retreives entry object by content hash"""
        ...

    def list_entries(
        self, *, limit: int, offset: int, run_id: int | None = None
    ) -> list[RegistryRecord]:
        """Lists entries as paginated"""
        ...

    def count_entries(self, *, run_id: int | None = None) -> int: ...


class PayloadStoreProtocol(Protocol):
    def save(self, *, phase: Phase, payload: bytes) -> str:
        """Persists content, returns an address referencing it."""
        ...

    def load(self, *, address: str) -> bytes:
        """Retrieves content previously stored at the given address."""
        ...
