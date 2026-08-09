import hashlib
from uuid import uuid4

from pluggle.enums import ContentFormat, MimeType
from pluggle.exceptions import errors
from pluggle.models.dto import ExtractableData


def generate_strategy_uid() -> str:
    """Return a 12-character identifier for an installed strategy.

    UUID4 rather than UUID7: truncating UUID7 would keep only its
    timestamp prefix and discard all randomness, making collisions
    certain within the same millisecond.
    """
    return uuid4().hex[:12]


def to_extractable(
    *, content: str | bytes, content_format: ContentFormat
) -> ExtractableData:
    if isinstance(content, str):
        content = content.encode()
    return ExtractableData(content=content, source_format=content_format)


def generate_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def content_format_to_mime(content_format: ContentFormat) -> MimeType:
    """Map a content format to its MIME type by shared enum member name.

    Image types exist in MimeType with no ContentFormat counterpart, so
    the reverse lookup raises for them by design.

    Raises:
        SerializationError: If the format has no MimeType counterpart.
    """
    try:
        return MimeType[content_format.name]
    except KeyError as e:
        raise errors.SerializationError(
            f"No MimeType mapping for ContentFormat '{content_format.name}'"
        ) from e


def mime_to_content_format(mime_type: MimeType) -> ContentFormat:
    """Map a MIME type to its content format by shared enum member name.

    Raises:
        SerializationError: If the MIME type has no ContentFormat
            counterpart, which is the case for image types.
    """
    try:
        return ContentFormat[mime_type.name]
    except KeyError as e:
        raise errors.SerializationError(
            f"No ContentFormat mapping for MimeType '{mime_type.name}'"
        ) from e
