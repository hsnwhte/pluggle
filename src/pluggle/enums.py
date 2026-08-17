import enum


class Phase(enum.Enum):
    """Pipeline phases, recorded per registry entry.

    A run uses either FETCH or DECODE depending on source type, and
    either LOAD or EXPORT depending on target type.
    """

    FETCH = "fetch"
    DECODE = "decode"
    EXTRACT = "extract"
    TRANSFORM = "transform"
    EXPORT = "export"
    LOAD = "load"


class RunStatus(enum.Enum):
    RUNNING = "running"
    COMPLETE = "complete"
    INTERRUPTED = "interrupted"


class ContentFormat(enum.Enum):
    """Formats Pluggle can decode, extract and write.

    Distinct from MimeType, which carries the wire-level strings used in
    HTTP headers. The two share member names where they overlap.
    """

    JSON = "json"
    XML = "xml"
    CSV = "csv"
    HTML = "html"
    DOCX = "docx"
    XLSX = "xlsx"
    PDF = "pdf"


class MimeType(enum.Enum):
    """MIME types as they appear in HTTP headers.

    Broader than ContentFormat: image types are included for outgoing
    Content-Type headers but have no decode or extract support.
    """

    JSON = "application/json"
    XML = "application/xml"
    CSV = "text/csv"
    HTML = "text/html"
    PNG = "image/png"
    JPEG = "image/jpeg"
    PDF = "application/pdf"
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class PluggleIOType(enum.Enum):
    API = "api"
    DB = "db"
    FILE = "file"


class CliListType(enum.Enum):
    RUNS = "runs"
    REGISTRY = "registry"
    STRATEGIES = "strategies"


class CliInspectType(enum.Enum):
    REGISTRY = "registry"
    PAYLOAD = "payload"


class DevEnvType(enum.Enum):
    DEV = "dev"
    REAL = "real"
