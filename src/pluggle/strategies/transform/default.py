from pluggle.enums import ContentFormat
from pluggle.models.dto import StrategyMeta, TransformableData, TransformedData


class TransformStrategySamplePassthrough:
    meta = StrategyMeta(name="default", version="v1.0")

    def __init__(
        self, *, target_format: ContentFormat, data: TransformableData, **kwargs
    ):
        self.target_format = target_format
        self.data = data

    def transform(self) -> TransformedData:
        return TransformedData(content=self.data.content)
