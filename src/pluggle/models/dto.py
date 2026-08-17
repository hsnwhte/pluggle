import re
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, computed_field, field_validator, model_validator

from pluggle.enums import ContentFormat, Phase, PluggleIOType, RunStatus


class StrategyMeta(BaseModel):
    name: str
    version: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", v):
            raise ValueError(
                f"Invalid strategy name '{v}'. Use lowercase letters, digits "
                f"and single hyphens between segments."
            )
        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        if not re.fullmatch(r"v\d+\.\d+", v):
            raise ValueError(f"Invalid version '{v}'. Expected format: vX.Y")
        return v


class InputArgs(BaseModel):
    model_config = {"frozen": True}
    source_type: PluggleIOType
    source_address: str
    source_table: str | None
    transform_strategy_name: str = "default_v1.0"
    target_type: PluggleIOType
    target_address: str
    target_table: str | None
    target_format: ContentFormat = ContentFormat.JSON

    @computed_field
    @property
    def source_as_path(self) -> Path:
        if self.source_type == PluggleIOType.FILE:
            return Path(self.source_address)
        else:
            raise AttributeError

    @computed_field
    @property
    def source_as_string(self) -> str:
        if self.source_type in (PluggleIOType.DB, PluggleIOType.API):
            return self.source_address
        else:
            raise AttributeError

    @computed_field
    @property
    def target_as_path(self) -> Path:
        if self.target_type == PluggleIOType.FILE:
            return Path(self.target_address)
        else:
            raise AttributeError

    @computed_field
    @property
    def target_as_string(self) -> str:
        if self.target_type in (PluggleIOType.DB, PluggleIOType.API):
            return self.target_address
        else:
            raise AttributeError

    @model_validator(mode="after")
    def check_table_names(self):
        if self.source_type == PluggleIOType.DB and self.source_table is None:
            raise ValueError("source_table is required when source_type is 'db'")
        if self.target_type == PluggleIOType.DB and self.target_table is None:
            raise ValueError("target_table is required when target_type is 'db'")
        return self


class FetchCacheData(BaseModel):
    model_config = {"frozen": True}
    api_url: str
    registry_address: int
    payload_address: str
    created_at: datetime
    is_active: bool


class PipelineRunRecordData(BaseModel):
    model_config = {"frozen": True}
    run_id: int
    started_at: datetime
    status: RunStatus
    interrupted_phase: Phase | None


class RegistryRecord(BaseModel):
    model_config = {"frozen": True}
    id: int
    run_id: int
    phase: Phase
    content_format: ContentFormat
    transform_strategy_name: str | None
    strategy_name: str
    content_hash: str
    address: str
    created_at: datetime
    is_active: bool


class ExtractableData(BaseModel):
    model_config = {"frozen": True}
    content: bytes
    source_format: ContentFormat


class TransformableData(BaseModel):
    model_config = {"frozen": True}
    content: bytes
    origin_format: ContentFormat


class TransformedData(BaseModel):
    model_config = {"frozen": True}
    content: bytes
