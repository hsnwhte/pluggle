from datetime import datetime

from sqlalchemy import CHAR, DateTime, LargeBinary, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from pluggle.enums import ContentFormat, Phase, RunStatus


class PluggleORM(DeclarativeBase):
    pass


class PipelineRunRecord(PluggleORM):
    __tablename__ = "pipeline_runs"
    run_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    status: Mapped[RunStatus] = mapped_column(
        SQLEnum(RunStatus), default=RunStatus.RUNNING
    )
    interrupted_phase: Mapped[Phase | None] = mapped_column(
        SQLEnum(Phase), nullable=True, default=None
    )


class RegistryEntry(PluggleORM):
    __tablename__ = "registry"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(index=True)
    phase: Mapped[Phase] = mapped_column(SQLEnum(Phase))
    content_format: Mapped[ContentFormat] = mapped_column(SQLEnum(ContentFormat))
    transform_strategy_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default=None
    )
    strategy_name: Mapped[str] = mapped_column(String(50))
    content_hash: Mapped[str] = mapped_column(CHAR(64), index=True)
    address: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    is_active: Mapped[bool] = mapped_column(default=True)


class FetchCache(PluggleORM):
    __tablename__ = "fetch_cache"
    api_url: Mapped[str] = mapped_column(primary_key=True)
    registry_address: Mapped[int]
    payload_address: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    is_active: Mapped[bool] = mapped_column(default=True)


class PayloadRecord(PluggleORM):
    __tablename__ = "payloads"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phase: Mapped[Phase] = mapped_column(SQLEnum(Phase))
    payload: Mapped[bytes] = mapped_column(LargeBinary)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
