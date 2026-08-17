import json

from pluggle.enums import ContentFormat
from pluggle.models.dto import StrategyMeta, TransformableData, TransformedData


class TransformStrategyForSampleCommentsJson:
    meta = StrategyMeta(name="strategy-for-sample-comments-json", version="v1.0")

    def __init__(
        self, *, target_format: ContentFormat, data: TransformableData, **kwargs
    ):
        self.target_format = target_format
        self.data = data

    def transform(self) -> TransformedData:
        rows = json.loads(self.data.content)
        new_rows = [
            {"data": f"id:{row['id']} | {row['name']} | {row['email']} | {row['body']}"}
            for row in rows
        ]
        transformed_content = json.dumps(new_rows).encode()

        return TransformedData(content=transformed_content)
