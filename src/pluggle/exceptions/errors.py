from pluggle.enums import Phase


# --- Root ---
class PluggleError(Exception):
    """Common ancestor for all errors raised by Pluggle."""


# --- Orchestration axis ---
class OrchestrationError(PluggleError):
    """Errors related to orchestration of pipeline phases."""


class InvalidInputError(OrchestrationError):
    """Errors stemming from invalid arguments/inputs by UI."""


class StrategyNotFoundError(OrchestrationError):
    """Errors occuring when selector is selecting strategies."""


# --- Diachronic axis: organized by pipeline phase ---
class FetchError(PluggleError):
    """Errors occurring while fetching data from a source."""


class FetchApiError(FetchError):
    """Errors occuring when fetching from an API Endpoint"""


class FetchBadRequestError(FetchApiError):
    """The request to the source was malformed (HTTP 400)."""

    def __init__(self, address: str):
        message = f"Bad request to source '{address}' (HTTP 400)."
        super().__init__(message)


class FetchNotAuthorizedError(FetchApiError):
    """Access to the specified source/address is unauthorized or forbidden (HTTP 401/403)."""

    def __init__(self, address: str, status_code: int):
        message = f"Not authorized to access source '{address}' (HTTP {status_code})."
        super().__init__(message)


class FetchNotFoundError(FetchApiError):
    """The specified source/address could not be found (HTTP 404)."""

    def __init__(self, address: str):
        message = f"Source '{address}' could not be found (HTTP 404)."
        super().__init__(message)


class FetchRateLimitError(FetchApiError):
    """The source rejected the request due to rate limiting (HTTP 429)."""

    def __init__(self, address: str):
        message = f"Rate limit exceeded when accessing source '{address}' (HTTP 429)."
        super().__init__(message)


class FetchServerError(FetchApiError):
    """The source's server encountered an error (HTTP 5xx)."""

    def __init__(self, address: str, status_code: int):
        message = f"Source '{address}' returned a server error (HTTP {status_code})."
        super().__init__(message)


class FetchContentTypeMissingError(FetchApiError):
    """Source API does not provide content-type data"""

    def __init__(self, address: str):
        message = f"Source '{address}' content-type is unknown."
        super().__init__(message)


class FetchDbError(FetchError):
    """Errors occuring when fetching from a Database"""


class FetchTableNameNotProvidedError(FetchDbError):
    def __init__(self):
        message = "No table name provided as argument for fetching from db."
        super().__init__(message)


class FetchDbUrlNotFoundError(FetchDbError):
    def __init__(self, db_url: str):
        message = f"Source url '{db_url}' not found."
        super().__init__(message)


class FetchTableNotFoundError(FetchDbError):
    def __init__(self, table_name: str):
        message = f"Table '{table_name}' not found in db."
        super().__init__(message)


class FetchTableSerializationError(FetchDbError):
    def __init__(self, table_name: str):
        message = f"Content from '{table_name}' could not be serialized into JSON."
        super().__init__(message)


class DecodeError(PluggleError):
    """Errors occurring while decoding raw data (reading file format)."""


class DecodeMalformedError(DecodeError):
    """The file does not conform to the expected format (malformed CSV/XML/JSON)."""


class DecodePermissionError(DecodeError):
    """Access to file is denied"""


class DecodeEmptyFileError(DecodeError):
    """The file is empty"""


class DecodeSourceFileNotFoundError(DecodeError):
    """Source file could not be found"""


class ExtractError(PluggleError):
    """Errors occurring while extracting decoded data into canonical form."""


class ExtractSyntaxError(ExtractError):
    """The content could not be parsed due to a syntax error."""


class TransformError(PluggleError):
    """Errors occurring while transforming canonical data into the
    target format. Transform strategies are entirely user-authored —
    Pluggle cannot diagnose the specific cause of a failure here.
    HINT: If you see a raw exception (KeyError, AttributeError, etc.)
    instead of a TransformError, check that your strategy's field
    mapping matches the actual shape of the data it receives.
    """


class LoadError(PluggleError):
    """Errors occurring while writing to the target."""


class LoadDbError(LoadError):
    """Errors occurring while loading to a db."""


class LoadTableNameNotProvidedError(LoadDbError):
    def __init__(self):
        message = "No table name provided as argument for inserting into the target db."
        super().__init__(message)


class LoadDbUrlNotFoundError(LoadDbError):
    def __init__(self, db_url: str):
        message = f"Target url '{db_url}' not found."
        super().__init__(message)


class LoadTableNotFoundError(LoadDbError):
    def __init__(self, table_name: str):
        message = f"Table '{table_name}' not found in the target db."
        super().__init__(message)


class LoadTableSerializationError(LoadDbError):
    def __init__(self, table_name: str):
        message = f"Content for '{table_name}' could not be deserialized from JSON."
        super().__init__(message)


class LoadApiError(LoadError):
    """Errors occurring when loading data to an API endpoint."""


class LoadBadRequestError(LoadApiError):
    """The request to the target was malformed (HTTP 400)."""

    def __init__(self, address: str):
        message = f"Bad request to target '{address}' (HTTP 400)."
        super().__init__(message)


class LoadNotAuthorizedError(LoadApiError):
    """Access to the specified target/address is unauthorized or forbidden (HTTP 401/403)."""

    def __init__(self, address: str, status_code: int):
        message = f"Not authorized to access target '{address}' (HTTP {status_code})."
        super().__init__(message)


class LoadNotFoundError(LoadApiError):
    """The specified target/address could not be found (HTTP 404)."""

    def __init__(self, address: str):
        message = f"Target '{address}' could not be found (HTTP 404)."
        super().__init__(message)


class LoadPayloadTooLargeError(LoadApiError):
    """The target rejected the request because the payload was too large (HTTP 413)."""

    def __init__(self, address: str):
        message = f"Payload too large when loading to target '{address}' (HTTP 413)."
        super().__init__(message)


class LoadRateLimitError(LoadApiError):
    """The target rejected the request due to rate limiting (HTTP 429)."""

    def __init__(self, address: str):
        message = f"Rate limit exceeded when accessing target '{address}' (HTTP 429)."
        super().__init__(message)


class LoadServerError(LoadApiError):
    """The target's server encountered an error (HTTP 5xx)."""

    def __init__(self, address: str, status_code: int):
        message = f"Target '{address}' returned a server error (HTTP {status_code})."
        super().__init__(message)


# --- Synchronic axis: organized by layer/technology, phase-independent ---


class SerializationError(PluggleError):
    """Errors occuring while serialization/type-conversion."""


class RegistryError(PluggleError):
    """Errors occurring while reading/writing the hash-based address registry."""


class RegistryEntryNotFoundError(RegistryError):
    """The requested registry entry does not exist or has been deactivated."""

    def __init__(
        self,
        *,
        entry_id: int | None = None,
        run_id: int | None = None,
        phase: Phase | None = None,
        content_hash: str | None = None,
    ):
        no_id_msg = f"No active registry entry at address {entry_id}"
        no_hash_msg = f"No active registry entry with hash {content_hash}"
        no_run_id_msg = f"No active registry entry with run_id {run_id} at phase {phase} could be found."
        if entry_id:
            super().__init__(no_id_msg)
        elif content_hash:
            super().__init__(no_hash_msg)
        else:
            super().__init__(no_run_id_msg)


class InvalidRegistryEntryError(RegistryError):
    """The requested registry entry could not be validated."""

    def __init__(
        self,
        *,
        entry_id: int | None = None,
        run_id: int | None = None,
        phase: Phase | None = None,
        content_hash: str | None = None,
    ):
        no_id_msg = f"Registry entry at address {entry_id} could not be validated."
        no_hash_msg = f"Registry entry with hash {content_hash} could not be validated."
        no_run_id_msg = f"Registry entry with run_id {run_id} at phase {phase} could not be validated."
        if entry_id:
            super().__init__(no_id_msg)
        elif content_hash:
            super().__init__(no_hash_msg)
        else:
            super().__init__(no_run_id_msg)


class StorageError(PluggleError):
    """Errors occurring while reading/writing payload data via a storage backend."""


class FetchCacheNotFoundError(StorageError):
    """Fetch cache does not exist or was deleted"""


class PayloadNotFoundError(StorageError):
    """The requested payload does not exist or has been deactivated."""


class StrategySetupError(PluggleError):
    """Errors related to set-up of transform strategies"""


class InvalidStrategyNameError(StrategySetupError):
    """Strategy name does not fit to the preset naming convension"""


class InvalidStrategyVersionError(StrategySetupError):
    """Strategy version does not fit to the preset naming convension"""
