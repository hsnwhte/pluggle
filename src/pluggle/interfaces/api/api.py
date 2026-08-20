import logging

from pluggle.exceptions import errors
from pluggle.models.dto import InputArgs, InstallReport
from pluggle.orchestrator import Orchestrator
from pluggle.strategies.transform import TRANSFORM_STRATEGY_MAP, strategy_manager

logger = logging.getLogger(__name__)


def run(input_args: InputArgs) -> int:
    """Run a full ETL pipeline from source to target."""
    orchestrator = Orchestrator(input_args=input_args)
    try:
        entry_id = orchestrator.run()
    except errors.PluggleError as e:
        logger.error(f"Pipeline FAILED: {e}")
        raise
    return entry_id


def list_available_strategies() -> list[str]:
    try:
        return [strategy for strategy in strategy_manager.get_repo_catalog()]
    except errors.StrategyNotFoundError:
        raise


def list_installed_strategies() -> list[str]:
    return sorted(TRANSFORM_STRATEGY_MAP)


def install_from_repo(repo_name: str) -> tuple[str, str | None]:
    """Install a strategy from the pluggle-strategies catalog by name."""
    try:
        return strategy_manager.install_from_repo(repo_name=repo_name)
    except errors.StrategySetupError, errors.StrategyNotFoundError:
        raise


def install_all_in_repo() -> InstallReport:
    try:
        return strategy_manager.install_all_in_repo()
    except errors.StrategyNotFoundError, errors.StrategySetupError:
        raise


def uninstall(strategy_name: str) -> None:
    try:
        strategy_manager.uninstall_strategy(strategy_name=strategy_name)
    except errors.StrategyNotFoundError:
        raise


def uninstall_all() -> None:
    try:
        strategy_manager.uninstall_all()
    except errors.StrategyNotFoundError:
        raise
