import logging

from pluggle import helpers, settings
from pluggle.enums import Phase, PluggleIOType, RunStatus
from pluggle.exceptions import errors
from pluggle.models.dto import (
    InputArgs,
    TransformableData,
    TransformedData,
)
from pluggle.processors.decoder import Decoder
from pluggle.processors.exporter import Exporter
from pluggle.processors.extractor import Extractor
from pluggle.processors.fetcher import Fetcher
from pluggle.processors.loader import Loader
from pluggle.processors.transformer import Transformer
from pluggle.selector import selector
from pluggle.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class Orchestrator:
    """Drives one pipeline run from source to target.

    Routes by IO type: file sources are decoded, API and DB sources are
    fetched (API results are served from the fetch cache when available).
    Extract and Transform then run for every route, and the result is
    either loaded or exported depending on target type.

    Owns its own UnitOfWork, so callers pass only input arguments.

    Args:
        input_args: Validated source, target, format and strategy settings.
    """
    def __init__(self, *, input_args: InputArgs):
        self.input_args = input_args
        self.uow = UnitOfWork()

    def run(self) -> int:
        """Execute the pipeline and return the final registry entry id.

        Registers a run, then walks the phases in order. On success,
        pipeline work is committed before the run is marked COMPLETE —
        the two sessions must not hold open write transactions at the
        same time, which SQLite rejects. On failure, pipeline work is
        rolled back, the run is marked INTERRUPTED with the failing
        phase, and the original exception propagates.

        Raises:
            PluggleError: Any pipeline failure, after the run is recorded
                as interrupted.
        """
        current_phase = None
        run_id: int = self.uow.run_records_store.register_run()
        logger.info(f"Initiating run: {run_id}")
        try:
            s_type = self.input_args.source_type
            s_address = self.input_args.source_address
            s_table = self.input_args.source_table

            if s_type == PluggleIOType.FILE:
                current_phase = Phase.DECODE
                logger.info(f"Decoding the {s_type.value}: '{s_address}'")
                last_entry_id = self._decode(run_id)
                logger.info(
                    f"{current_phase.value.upper()} successful, registry entry id: {last_entry_id}"
                )

            elif s_type == PluggleIOType.DB:
                current_phase = Phase.FETCH
                logger.info(f"Fetching from {s_type.value}: '{s_address} - {s_table}'")
                last_entry_id = self._fetch(run_id)
                logger.info(
                    f"{current_phase.value.upper()} successful, registry entry id: {last_entry_id}"
                )

            else:
                current_phase = Phase.FETCH
                logger.info("Checking fetch cache...")
                try:
                    cache = self.uow.fetch_cache_store.load(api_url=s_address)
                    last_entry_id = cache.registry_address
                    logger.info(
                        f"Found cached data for url '{s_address}' at registry entry id:"
                        f"{last_entry_id}"
                    )

                except errors.FetchCacheNotFoundError:
                    logger.info(f"No cache data found for url '{s_address}'")
                    logger.info("Fetching data from source...")
                    last_entry_id = self._fetch(run_id)
                    logger.info(
                        f"{current_phase.value.upper()} successful, registry entry id: {last_entry_id}"
                    )

            current_phase = Phase.EXTRACT
            logger.info("Extracting data...")
            last_entry_id = self._extract(run_id, last_entry_id)
            logger.info(
                f"{current_phase.value.upper()} successful, registry entry id: {last_entry_id}"
            )

            current_phase = Phase.TRANSFORM
            logger.info(
                f"Transforming data based on strategy: '{self.input_args.transform_strategy_name}'"
            )
            last_entry_id = self._transform(run_id, last_entry_id)
            logger.info(
                f"{current_phase.value.upper()} successful, registry entry id: {last_entry_id}"
            )

            if self.input_args.target_type.value in ("api", "db"):
                current_phase = Phase.LOAD
                logger.info(
                    f"Loading to {self.input_args.target_type.value}: "
                    f"'{self.input_args.target_address}'"
                )
                last_entry_id = self._load(run_id, last_entry_id)
                self.uow.commit()
                self.uow.run_records_store.update_record(
                    run_id=run_id, status=RunStatus.COMPLETE
                )
                logger.info(
                    f"{current_phase.value.upper()} successful, registry entry id: {last_entry_id}"
                )
                return last_entry_id
            elif self.input_args.target_type.value == "file":
                current_phase = Phase.EXPORT
                logger.info(
                    f"Exporting to {self.input_args.target_type.value}: "
                    f"'{self.input_args.target_address}'"
                )
                last_entry_id = self._export(run_id, last_entry_id)
                self.uow.commit()
                self.uow.run_records_store.update_record(
                    run_id=run_id, status=RunStatus.COMPLETE
                )
                logger.info(
                    f"{current_phase.value.upper()} successful, registry entry id: {last_entry_id}"
                )
                return last_entry_id
            else:
                raise errors.InvalidInputError()
        except Exception:
            self.uow.rollback()
            self.uow.run_records_store.update_record(
                run_id=run_id,
                status=RunStatus.INTERRUPTED,
                phase=current_phase,
            )
            raise
        finally:
            self.uow.pipeline_session.close()
            self.uow.run_records_session.close()

    def _export(self, run_id: int, entry_id: int) -> int:
        entry = self.uow.registry_store.get_entry_by_id(entry_id=entry_id)
        content_bytes = self.uow.payload_store.load(address=entry.address)
        transformed_content = TransformedData(content=content_bytes)

        export_strategy = selector.get_export_strategy()
        logger.debug(f"Applying strategy: '{export_strategy.__name__}'")
        exporter = Exporter(
            file_path=self.input_args.target_as_path, strategy=export_strategy
        )
        exporter.export(data=transformed_content)

        export_entry_id = self.uow.registry_store.save_entry(
            run_id=run_id,
            phase=Phase.EXPORT,
            content_format=self.input_args.target_format,
            transform_strategy_name=self.input_args.transform_strategy_name,
            strategy_name=export_strategy.__name__,
            content_hash=helpers.generate_hash(content=content_bytes),
            address=str(self.input_args.target_address),
        )
        return export_entry_id

    def _load(self, run_id: int, entry_id: int) -> int:
        entry = self.uow.registry_store.get_entry_by_id(entry_id=entry_id)
        content_bytes = self.uow.payload_store.load(address=entry.address)
        transformed_content = TransformedData(content=content_bytes)

        load_strategy = selector.get_load_strategy(self.input_args.target_type)
        logger.debug(f"Applying strategy: '{load_strategy.__name__}'")

        loader = Loader(
            address=self.input_args.target_address,
            strategy=load_strategy,
            target_format=self.input_args.target_format,
            table_name=self.input_args.target_table,
        )
        loader.load(data=transformed_content)

        load_entry_id = self.uow.registry_store.save_entry(
            run_id=run_id,
            phase=Phase.LOAD,
            content_format=self.input_args.target_format,
            strategy_name=load_strategy.__name__,
            content_hash=helpers.generate_hash(content=content_bytes),
            address=str(self.input_args.target_address),
        )
        return load_entry_id

    def _extract(self, run_id: int, entry_id: int) -> int:
        entry = self.uow.registry_store.get_entry_by_id(entry_id=entry_id)
        extract_strategy = selector.get_extract_strategy(entry.content_format)
        logger.debug(f"Applying strategy: '{extract_strategy.__name__}'")
        content_bytes = self.uow.payload_store.load(address=entry.address)
        extractor = Extractor(content=content_bytes, strategy=extract_strategy)
        data = extractor.extract()

        payload_address = self.uow.payload_store.save(
            phase=Phase.EXTRACT, payload=data.content
        )

        extr_entry_id = self.uow.registry_store.save_entry(
            run_id=run_id,
            phase=Phase.EXTRACT,
            content_format=settings.NORMALIZED_FORMAT,
            strategy_name=extract_strategy.__name__,
            content_hash=helpers.generate_hash(content=data.content),
            address=str(payload_address),
        )
        return extr_entry_id

    def _transform(self, run_id: int, entry_id: int) -> int:
        entry = self.uow.registry_store.get_entry_by_id(entry_id=entry_id)
        content_bytes = self.uow.payload_store.load(address=entry.address)
        transformable_content = TransformableData(
            content=content_bytes, origin_format=entry.content_format
        )

        transform_strategy_class = selector.get_transform_strategy(
            self.input_args.transform_strategy_name,
        )
        transform_strategy = transform_strategy_class(
            target_format=self.input_args.target_format, data=transformable_content
        )
        logger.debug(f"Applying strategy: '{transform_strategy_class.__name__}'")
        transformer = Transformer(strategy=transform_strategy)
        data = transformer.transform()

        payload_address = self.uow.payload_store.save(
            phase=Phase.TRANSFORM, payload=data.content
        )

        trns_entry_id = self.uow.registry_store.save_entry(
            run_id=run_id,
            phase=Phase.TRANSFORM,
            content_format=self.input_args.target_format,
            transform_strategy_name=self.input_args.transform_strategy_name,
            strategy_name=transform_strategy.__class__.__name__,
            content_hash=helpers.generate_hash(content=data.content),
            address=str(payload_address),
        )
        return trns_entry_id

    def _decode(self, run_id: int) -> int:
        decode_strategy = selector.get_decode_strategy(self.input_args.source_as_path)
        logger.debug(f"Applying strategy: '{decode_strategy.__name__}'")
        decoder = Decoder(
            source_address=self.input_args.source_as_path, strategy=decode_strategy
        )
        data = decoder.decode()
        payload_address = self.uow.payload_store.save(
            phase=Phase.DECODE, payload=data.content
        )

        entry_id = self.uow.registry_store.save_entry(
            run_id=run_id,
            phase=Phase.DECODE,
            content_format=data.source_format,
            strategy_name=decode_strategy.__name__,
            content_hash=helpers.generate_hash(content=data.content),
            address=str(payload_address),
        )
        return entry_id

    def _fetch(self, run_id: int) -> int:
        """Fetch from an API or DB source and register the result.

        API fetches are additionally written to the fetch cache, so a
        later run against the same URL can reuse the stored payload.
        """
        fetch_strategy = selector.get_fetch_strategy(self.input_args.source_type)
        logger.debug(f"Applying strategy: '{fetch_strategy.__name__}'")

        fetcher = Fetcher(
            source_address=self.input_args.source_address,
            strategy=fetch_strategy,
            table_name=self.input_args.source_table,
        )
        data = fetcher.fetch()
        payload_address = self.uow.payload_store.save(
            phase=Phase.FETCH, payload=data.content
        )

        entry_id = self.uow.registry_store.save_entry(
            run_id=run_id,
            phase=Phase.FETCH,
            content_format=data.source_format,
            strategy_name=fetch_strategy.__name__,
            content_hash=helpers.generate_hash(content=data.content),
            address=str(payload_address),
        )
        if self.input_args.source_type == PluggleIOType.API:
            self.uow.fetch_cache_store.save(
                api_url=self.input_args.source_address,
                registry_address=entry_id,
                payload_address=payload_address,
            )

        return entry_id
