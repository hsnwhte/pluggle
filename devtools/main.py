import json
import logging
import os
from dataclasses import asdict

import typer
from pydantic import ValidationError

from devtools import settings as dev_settings

os.environ["PLUGGLE_STORE_ADDRESS"] = dev_settings.DEV_RUNTIME_POSTGRE

from devtools.test_packages import TEST_PACKAGES
from devtools.tools import db_tools
from pluggle.enums import ContentFormat, DevEnvType, PluggleIOType
from pluggle.exceptions import errors
from pluggle.logging_config import setup_logging
from pluggle.models.dto import InputArgs
from pluggle.orchestrator import Orchestrator
from pluggle.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)
dev = typer.Typer()


@dev.callback()
def callback(debug: bool = typer.Option(False, "--debug", "-d")):
    setup_logging(debug=debug)


@dev.command(name="test")
def test(
    inject_test_pack: int = typer.Option(None, "--test-pack", "-i"),
    source_type: PluggleIOType = typer.Option(None, "--source-type", "-soty"),
    source_address: str = typer.Option(None, "--source-address", "-soad"),
    target_type: PluggleIOType = typer.Option(None, "--target-type", "-taty"),
    target_address: str = typer.Option(None, "--target-address", "-taad"),
    transform_strategy_name: str = typer.Option(None, "--transform-strategy", "-ts"),
    source_table: str = typer.Option(None, "--source-table", "-sota"),
    target_table: str = typer.Option(None, "--target-table", "-tata"),
    target_format: ContentFormat = typer.Option(
        ContentFormat.JSON, "--target-format", "-tafo"
    ),
):

    if inject_test_pack:
        try:
            pack = TEST_PACKAGES.get(inject_test_pack, None)
            if pack is None:
                typer.echo(
                    f"Test package '{inject_test_pack}' could not be found.", err=True
                )
                raise typer.Exit(code=1)
            input_args = InputArgs(**asdict(pack))
        except (ValidationError, AttributeError) as e:
            logger.error(f"Invalid input: {e}")
            typer.echo(f"Invalid input: {e}", err=True)
            raise typer.Exit(code=1)
    else:
        try:
            input_args = InputArgs(
                source_type=source_type,
                source_address=source_address,
                source_table=source_table,
                target_type=target_type,
                target_address=target_address,
                target_table=target_table,
                target_format=target_format,
                transform_strategy_name=transform_strategy_name,
            )
        except (ValidationError, AttributeError) as e:
            logger.error(f"Invalid input: {e}")
            typer.echo(f"Invalid input: {e}", err=True)
            raise typer.Exit(code=1)

    orchestrator = Orchestrator(input_args=input_args)
    logger.debug("Orchestrator object instantiated")
    logger.info("Pipeline starting...")
    try:
        entry_id = orchestrator.run()
    except errors.PluggleError as e:
        logger.exception(f"Pipeline failed: {e}")
        typer.echo(f"Pipeline failed: {e}", err=True)
        raise typer.Exit(code=1)

    logger.info(f"Pipeline finished successfully, final registry entry id: {entry_id}")
    typer.echo(f"Success. Final registry entry id: {entry_id}")


@dev.command(name="inspect")
def inspect(
    payload_id: int = typer.Option(..., "--payload-id", "-p"),
):
    engine = db_tools.get_engine(url=dev_settings.DEV_RUNTIME_POSTGRE, echo=False)
    with UnitOfWork(engine=engine) as uow:
        try:
            raw_content = uow.payload_store.load(address=str(payload_id))
        except errors.PayloadNotFoundError as e:
            typer.echo(f"Payload not found: {e}", err=True)
            raise typer.Exit(code=1)

        try:
            parsed = json.loads(raw_content)
            typer.echo(json.dumps(parsed, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            typer.echo(raw_content.decode(errors="replace"))


@dev.command(name="setup-test-env")
def setup_test_env():
    eng_runtime = db_tools.get_engine(url=dev_settings.DEV_RUNTIME_POSTGRE, echo=True)
    db_tools.create_all_runtime_tables(engine=eng_runtime)
    eng_src = db_tools.get_engine(url=dev_settings.DEV_SOURCE_DB_URL, echo=True)
    db_tools.create_all_source_tables(engine=eng_src)
    eng_trg = db_tools.get_engine(url=dev_settings.DEV_TARGET_DB_URL, echo=True)
    db_tools.create_all_target_tables(engine=eng_trg)


@dev.command(name="reset-test-env")
def reset_test_env():
    eng_runtime = db_tools.get_engine(url=dev_settings.DEV_RUNTIME_POSTGRE, echo=True)
    db_tools.reset_all_runtime_tables(engine=eng_runtime)
    eng_src = db_tools.get_engine(url=dev_settings.DEV_SOURCE_DB_URL, echo=True)
    db_tools.reset_all_source_tables(engine=eng_src)
    eng_trg = db_tools.get_engine(url=dev_settings.DEV_TARGET_DB_URL, echo=True)
    db_tools.reset_all_target_tables(engine=eng_trg)


@dev.command(name="hard-reset-test-env")
def hard_reset_test_env():
    eng_runtime = db_tools.get_engine(url=dev_settings.DEV_RUNTIME_POSTGRE, echo=True)
    db_tools.drop_all_runtime_tables(engine=eng_runtime)
    eng_src = db_tools.get_engine(url=dev_settings.DEV_SOURCE_DB_URL, echo=True)
    db_tools.drop_all_source_tables(engine=eng_src)
    eng_trg = db_tools.get_engine(url=dev_settings.DEV_TARGET_DB_URL, echo=True)
    db_tools.drop_all_target_tables(engine=eng_trg)


@dev.command(name="reset-runtime-db")
def reset_runtime_db(
    env: DevEnvType = typer.Option(DevEnvType.DEV, "--env", "-e"),
):
    url = (
        dev_settings.DEV_RUNTIME_POSTGRE
        if env == DevEnvType.DEV
        else dev_settings.REAL_RUNTIME_STORE
    )
    eng_runtime = db_tools.get_engine(url=url, echo=True)
    db_tools.reset_all_runtime_tables(engine=eng_runtime)


if __name__ == "__main__":
    dev()
