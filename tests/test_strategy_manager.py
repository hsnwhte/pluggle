import shutil

import httpx
import pytest

from pluggle.exceptions import errors
from pluggle.strategies.transform import strategy_manager

VALID_STRATEGY = """
from pluggle.models.dto import StrategyMeta


class TransformStrategy{suffix}:
    meta = StrategyMeta(name="{name}", version="{version}")

    def __init__(self, *, target_format=None, data=None, **kwargs):
        self.data = data

    def transform(self):
        return self.data
"""


@pytest.fixture
def installed_dir(tmp_path, monkeypatch):
    """Redirect installs to a temp directory instead of the real one."""
    target = tmp_path / "installed"
    target.mkdir()
    monkeypatch.setattr(strategy_manager, "INSTALLED_STRATEGIES_DIR", target)
    return target


@pytest.fixture
def make_strategy(tmp_path):
    """Write a valid strategy file and return its path."""

    def _make(name="sample-mapper", version="v1.0", suffix="Sample", filename=None):
        path = tmp_path / (filename or f"{name}_{version}_src.py")
        path.write_text(
            VALID_STRATEGY.format(suffix=suffix, name=name, version=version)
        )
        return path

    return _make


class FakeResponse:
    def __init__(self, *, json_data=None, content=b""):
        self._json_data = json_data
        self.content = content

    def raise_for_status(self):
        return None

    def json(self):
        return self._json_data


# --- _load_strategy_from_file


def test_load_strategy_returns_class(make_strategy):
    strategy = strategy_manager._load_strategy_from_file(file_path=make_strategy())

    assert strategy.meta.name == "sample-mapper"
    assert strategy.meta.version == "v1.0"


def test_load_strategy_missing_file(tmp_path):
    with pytest.raises(errors.StrategyNotFoundError):
        strategy_manager._load_strategy_from_file(file_path=tmp_path / "nope.py")


def test_load_strategy_syntax_error(tmp_path):
    path = tmp_path / "broken.py"
    path.write_text("class TransformStrategyBroken(:\n")

    with pytest.raises(errors.StrategyNotFoundError):
        strategy_manager._load_strategy_from_file(file_path=path)


def test_load_strategy_no_matching_class(tmp_path):
    path = tmp_path / "empty.py"
    path.write_text("class SomethingElse:\n    pass\n")

    with pytest.raises(errors.StrategyNotFoundError):
        strategy_manager._load_strategy_from_file(file_path=path)


def test_load_strategy_multiple_matching_classes(tmp_path):
    path = tmp_path / "two.py"
    path.write_text(
        "class TransformStrategyOne:\n    pass\n\n"
        "class TransformStrategyTwo:\n    pass\n"
    )

    with pytest.raises(errors.StrategyNotFoundError):
        strategy_manager._load_strategy_from_file(file_path=path)


def test_load_strategy_without_meta(tmp_path):
    path = tmp_path / "no_meta.py"
    path.write_text(
        "class TransformStrategyNoMeta:\n    def transform(self):\n        pass\n"
    )

    with pytest.raises(errors.StrategyNotFoundError):
        strategy_manager._load_strategy_from_file(file_path=path)


# --- install_from_path


def test_install_from_path_copies_file_and_returns_name(installed_dir, make_strategy):
    name = strategy_manager.install_from_path(file_path=make_strategy())

    assert name == "sample-mapper_v1.0"
    assert (installed_dir / "sample-mapper_v1.0.py").exists()


def test_install_from_path_rejects_duplicate(installed_dir, make_strategy):
    source = make_strategy()
    strategy_manager.install_from_path(file_path=source)

    with pytest.raises(errors.StrategySetupError):
        strategy_manager.install_from_path(file_path=source)


def test_install_from_path_allows_second_version(installed_dir, make_strategy):
    strategy_manager.install_from_path(file_path=make_strategy(version="v1.0"))
    strategy_manager.install_from_path(file_path=make_strategy(version="v2.0"))

    assert (installed_dir / "sample-mapper_v1.0.py").exists()
    assert (installed_dir / "sample-mapper_v2.0.py").exists()


# --- get_repo_catalog


def test_get_repo_catalog_returns_entries(monkeypatch):
    entries = {"sample-mapper_v1.0": {"file": "strategies/sample-mapper_v1.0.py"}}
    monkeypatch.setattr(
        httpx, "get", lambda *a, **kw: FakeResponse(json_data={"strategies": entries})
    )

    assert strategy_manager.get_repo_catalog() == entries


def test_get_repo_catalog_without_strategies_key(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **kw: FakeResponse(json_data={}))

    assert strategy_manager.get_repo_catalog() == {}


def test_get_repo_catalog_network_failure(monkeypatch):
    def boom(*args, **kwargs):
        raise httpx.HTTPError("unreachable")

    monkeypatch.setattr(httpx, "get", boom)

    with pytest.raises(errors.StrategyNotFoundError):
        strategy_manager.get_repo_catalog()


# --- _fetch_strategy_from_repo


def test_fetch_unknown_strategy_name():
    with pytest.raises(errors.StrategyNotFoundError):
        strategy_manager._fetch_strategy_from_repo(
            catalog_entries={}, strategy_name="missing_v1.0"
        )


def test_fetch_writes_file_and_derives_doc_url(monkeypatch, make_strategy):
    source = make_strategy()
    entries = {"sample-mapper_v1.0": {"file": "strategies/sample-mapper_v1.0.py"}}
    monkeypatch.setattr(
        httpx, "get", lambda *a, **kw: FakeResponse(content=source.read_bytes())
    )

    path, doc_url = strategy_manager._fetch_strategy_from_repo(
        catalog_entries=entries, strategy_name="sample-mapper_v1.0"
    )

    assert path.read_bytes() == source.read_bytes()
    assert doc_url.endswith("/strategies/sample-mapper_v1.0.md")


def test_fetch_download_failure(monkeypatch):
    def boom(*args, **kwargs):
        raise httpx.HTTPError("unreachable")

    monkeypatch.setattr(httpx, "get", boom)

    with pytest.raises(errors.StrategyNotFoundError):
        strategy_manager._fetch_strategy_from_repo(
            catalog_entries={"a_v1.0": {"file": "strategies/a_v1.0.py"}},
            strategy_name="a_v1.0",
        )


# --- install_from_repo


def test_install_from_repo(installed_dir, make_strategy, monkeypatch):
    source = make_strategy()
    entries = {"sample-mapper_v1.0": {"file": "strategies/sample-mapper_v1.0.py"}}
    monkeypatch.setattr(strategy_manager, "get_repo_catalog", lambda: entries)
    monkeypatch.setattr(
        httpx, "get", lambda *a, **kw: FakeResponse(content=source.read_bytes())
    )

    name, doc_url = strategy_manager.install_from_repo(repo_name="sample-mapper_v1.0")

    assert name == "sample-mapper_v1.0"
    assert doc_url.endswith(".md")
    assert (installed_dir / "sample-mapper_v1.0.py").exists()


def test_install_from_repo_unknown_name(installed_dir, monkeypatch):
    monkeypatch.setattr(strategy_manager, "get_repo_catalog", lambda: {})

    with pytest.raises(errors.StrategyNotFoundError):
        strategy_manager.install_from_repo(repo_name="missing_v1.0")


# --- install_all_in_repo


def test_install_all_installs_everything(installed_dir, make_strategy, monkeypatch):
    entries = {
        "sample-mapper_v1.0": {"file": "strategies/sample-mapper_v1.0.py"},
        "other-mapper_v1.0": {"file": "strategies/other-mapper_v1.0.py"},
    }
    sources = {
        "sample-mapper_v1.0": make_strategy(name="sample-mapper", suffix="Sample"),
        "other-mapper_v1.0": make_strategy(name="other-mapper", suffix="Other"),
    }

    def fake_get(url, *args, **kwargs):
        key = url.rsplit("/", 1)[-1].removesuffix(".py")
        return FakeResponse(content=sources[key].read_bytes())

    monkeypatch.setattr(strategy_manager, "get_repo_catalog", lambda: entries)
    monkeypatch.setattr(httpx, "get", fake_get)

    report = strategy_manager.install_all_in_repo()

    assert report.total == 2
    assert report.skipped == 0
    assert sorted(report.installed) == ["other-mapper_v1.0", "sample-mapper_v1.0"]
    assert (installed_dir / "sample-mapper_v1.0.py").exists()
    assert (installed_dir / "other-mapper_v1.0.py").exists()


def test_install_all_skips_already_installed(installed_dir, make_strategy, monkeypatch):
    entries = {"sample-mapper_v1.0": {"file": "strategies/sample-mapper_v1.0.py"}}
    shutil.copy(make_strategy(), installed_dir / "sample-mapper_v1.0.py")
    monkeypatch.setattr(strategy_manager, "get_repo_catalog", lambda: entries)

    report = strategy_manager.install_all_in_repo()

    assert report.total == 1
    assert report.skipped == 1
    assert report.installed == []


def test_install_all_on_empty_catalog(installed_dir, monkeypatch):
    monkeypatch.setattr(strategy_manager, "get_repo_catalog", lambda: {})

    report = strategy_manager.install_all_in_repo()

    assert report.total == 0
    assert report.skipped == 0
    assert report.installed == []


# --- uninstall


def test_uninstall_removes_file(installed_dir, make_strategy):
    name = strategy_manager.install_from_path(file_path=make_strategy())

    strategy_manager.uninstall_strategy(strategy_name=name)

    assert not (installed_dir / f"{name}.py").exists()


def test_uninstall_unknown_strategy(installed_dir):
    with pytest.raises(errors.StrategyNotFoundError):
        strategy_manager.uninstall_strategy(strategy_name="missing_v1.0")


def test_uninstall_all_removes_everything(installed_dir, make_strategy):
    strategy_manager.install_from_path(file_path=make_strategy(version="v1.0"))
    strategy_manager.install_from_path(file_path=make_strategy(version="v2.0"))

    strategy_manager.uninstall_all()

    assert list(installed_dir.glob("*.py")) == []


def test_uninstall_all_when_empty(installed_dir):
    with pytest.raises(errors.StrategyNotFoundError):
        strategy_manager.uninstall_all()
