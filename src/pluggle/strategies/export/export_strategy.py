import json
from pathlib import Path

from pluggle.models.dto import TransformedData


class ExportStrategy:
    @staticmethod
    def export(*, data: TransformedData, file_path: Path) -> None:
        try:
            formatted = json.dumps(
                json.loads(data.content), indent=2, ensure_ascii=False
            ).encode()
            file_path.write_bytes(formatted)
        except json.JSONDecoder:
            file_path.write_bytes(data.content)
