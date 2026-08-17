import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from pluggle.enums import ContentFormat, Phase, RunStatus
from pluggle.exceptions import errors
from pluggle.helpers import generate_hash
from pluggle.models.orm import PipelineRunRecord, PluggleORM
from pluggle.storage.backend import (
    FetchCacheStore,
    PayloadStore,
    PipelineRunRecords,
    RegistryStore,
)

POSTGRES_URL = "postgresql://postgres:testpass@localhost:5432/postgres"


@pytest.fixture(
    scope="session", params=["sqlite", "postgres"], ids=["sqlite", "postgres"]
)
def test_engine(request):
    if request.param == "sqlite":
        engine = create_engine("sqlite:///:memory:")
        PluggleORM.metadata.create_all(engine)
        yield engine
    else:
        engine = create_engine(POSTGRES_URL)
        PluggleORM.metadata.drop_all(engine)
        PluggleORM.metadata.create_all(engine, checkfirst=True)
        yield engine
        PluggleORM.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_session(test_engine: Engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def registry_entry_kwargs():
    return {
        "run_id": 1,
        "phase": Phase.FETCH,
        "content_format": ContentFormat.JSON,
        "strategy_name": "db_fetch_strategy",
        "content_hash": generate_hash(content="test".encode()),
        "address": "1",
    }


@pytest.fixture
def registry_store(test_session: Session):
    return RegistryStore(session=test_session)


@pytest.fixture
def saved_registry_entry(registry_store: RegistryStore, registry_entry_kwargs: dict):
    entry_id = registry_store.save_entry(**registry_entry_kwargs)
    return entry_id, registry_entry_kwargs


@pytest.fixture
def payload_store(test_session: Session):
    return PayloadStore(session=test_session)


@pytest.fixture
def fetch_cache_store(test_session: Session):
    return FetchCacheStore(session=test_session)


def test_pipeline_run_records_register_run(test_session: Session):
    store = PipelineRunRecords(session=test_session)

    run_id = store.register_run()

    assert isinstance(run_id, int)


def test_pipeline_run_records_update_record(test_session: Session):
    store = PipelineRunRecords(session=test_session)
    run_id = store.register_run()

    store.update_record(
        run_id=run_id, status=RunStatus.INTERRUPTED, phase=Phase.TRANSFORM
    )
    updated = test_session.get(PipelineRunRecord, run_id)

    assert updated is not None
    assert updated.status == RunStatus.INTERRUPTED
    assert updated.interrupted_phase == Phase.TRANSFORM


def test_registry_store_save_entry(test_session: Session, registry_entry_kwargs: dict):
    store = RegistryStore(session=test_session)

    entry_id = store.save_entry(**registry_entry_kwargs)

    assert isinstance(entry_id, int)


def test_registry_store_get_entry_by_id(
    saved_registry_entry: tuple[int, dict],
    registry_store: RegistryStore,
):
    entry_id, kwargs = saved_registry_entry

    data = registry_store.get_entry_by_id(entry_id=entry_id)

    assert data.id == entry_id
    assert data.run_id == kwargs["run_id"]
    assert data.phase == kwargs["phase"]
    assert data.content_format == kwargs["content_format"]
    assert data.strategy_name == kwargs["strategy_name"]
    assert data.content_hash == kwargs["content_hash"]
    assert data.address == kwargs["address"]


def test_registry_store_get_entry_by_run_id(
    saved_registry_entry: tuple[int, dict],
    registry_store: RegistryStore,
):
    entry_id, kwargs = saved_registry_entry

    data = registry_store.get_entry_by_run_id(
        run_id=kwargs["run_id"], phase=kwargs["phase"]
    )

    assert data.id == entry_id
    assert data.run_id == kwargs["run_id"]
    assert data.phase == kwargs["phase"]
    assert data.strategy_name == kwargs["strategy_name"]
    assert data.content_hash == kwargs["content_hash"]
    assert data.address == kwargs["address"]


def test_registry_store_get_entry_by_content_hash(
    saved_registry_entry: tuple[int, dict],
    registry_store: RegistryStore,
):
    entry_id, kwargs = saved_registry_entry

    data = registry_store.get_entry_by_hash(content_hash=kwargs["content_hash"])

    assert data.id == entry_id
    assert data.run_id == kwargs["run_id"]
    assert data.phase == kwargs["phase"]
    assert data.strategy_name == kwargs["strategy_name"]
    assert data.content_hash == kwargs["content_hash"]
    assert data.address == kwargs["address"]


def test_payload_store_save(payload_store: PayloadStore):
    phase = Phase.FETCH
    payload = "test".encode()

    record_id_str = payload_store.save(phase=phase, payload=payload)

    assert isinstance(record_id_str, str)


def test_payload_store_load(payload_store: PayloadStore):
    phase = Phase.FETCH
    payload = "test".encode()
    address = payload_store.save(phase=phase, payload=payload)

    loaded = payload_store.load(address=address)

    assert isinstance(loaded, bytes)
    assert loaded == "test".encode()


def test_fetch_cache_store_save(fetch_cache_store: FetchCacheStore):
    result = fetch_cache_store.save(
        api_url="https://example.com/api", registry_address=1, payload_address="1"
    )
    assert result == "https://example.com/api"


def test_fetch_cache_store_load_success(fetch_cache_store: FetchCacheStore):
    fetch_cache_store.save(
        api_url="https://example.com/api", registry_address=1, payload_address="1"
    )

    result = fetch_cache_store.load(api_url="https://example.com/api")

    assert result.api_url == "https://example.com/api"
    assert result.registry_address == 1
    assert result.payload_address == "1"


def test_fetch_cache_store_load_not_found(fetch_cache_store: FetchCacheStore):
    with pytest.raises(errors.FetchCacheNotFoundError):
        fetch_cache_store.load(api_url="https://nonexistent.com")
