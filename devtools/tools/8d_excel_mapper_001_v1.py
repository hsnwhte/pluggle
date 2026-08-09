# Licensed under the MIT License. See:
# https://github.com/hsnwhte/pluggle-strategies/blob/main/LICENSE

import json
from datetime import date, timedelta
from typing import TypeVar

from pydantic import BaseModel, ValidationError, model_validator

from pluggle.enums import ContentFormat
from pluggle.exceptions import errors
from pluggle.models.dto import TransformableData, TransformedData

M = TypeVar("M", bound=BaseModel)

COORDS = {
    "date_open": "G5",
    "no": "J5",
    "customer": "D7",
    "initial_response": "G7",
    "customer_complaint_no": "J7",
    "address": "D9",
    "target_close_date": "G9",
    "location": "D11",
    "revision_dates": "G11",
    "part_no": "D13",
    "initiator": "G13",
    "product_name": "D15",
    "initiator_spvr": "G15",
    "actual_close_date": "G17",
    "champion": "D21",
    "problem_statement": "F21",
    "team_leader": "D23",
    "team_members": "D25",
    "ica_description": "C31",
    "ica_effective": "I31",
    "ica_target_date": "J31",
    "ica_actual_date": "K31",
    "rc_description": "C40",
    "rc_contribution": "J40",
    "choose_pca_description": "C48",
    "choose_pca_effective": "J48",
    "implement_pca_description": "C56",
    "implement_pca_target_date": "J56",
    "implement_pca_actual_date": "K56",
    "spa_description": "C64",
    "spa_target_date": "J64",
    "spa_actual_date": "K64",
}

COORDS_SET = set(COORDS.values())

CHECKBOXES = {
    "internal": "xl/ctrlProps/ctrlProps10.xml",
    "external": "xl/ctrlProps/ctrlProps11.xml",
    "control_plan": "xl/ctrlProps/ctrlProps12.xml",
    "fmea": "xl/ctrlProps/ctrlProps13.xml",
    "flowchart": "xl/ctrlProps/ctrlProps14.xml",
    "proc_work_instr": "xl/ctrlProps/ctrlProps15.xml",
    "add_to_internal_audit": "xl/ctrlProps/ctrlProps16.xml",
}


def excel_serial_to_date(serial: int) -> date:
    epoch = date(1899, 12, 30)
    return epoch + timedelta(days=serial)


class DocMeta(BaseModel):
    title: str = "8D Problem Solving"
    no: str | None = None
    date_open: str | date | None = None
    internal: bool = False
    external: bool = False
    customer_complaint_no: str | None = None
    initial_response: str | None = None
    target_close_date: str | date | None = None
    revision_dates: str | date | None = None
    actual_close_date: str | date | None = None
    initiator: str | None = None
    initiator_spvr: str | None = None

    @model_validator(mode="after")
    def serialize_dates(self):
        if isinstance(self.date_open, str):
            self.date_open = excel_serial_to_date(int(self.date_open))
        if isinstance(self.target_close_date, str):
            self.target_close_date = excel_serial_to_date(int(self.target_close_date))
        if isinstance(self.revision_dates, str):
            self.revision_dates = excel_serial_to_date(int(self.revision_dates))
        if isinstance(self.actual_close_date, str):
            self.actual_close_date = excel_serial_to_date(int(self.actual_close_date))
        return self


class Definitions(BaseModel):
    title: str = "Who is Impacted by the Problem?"
    customer: str | None = None
    address: str | None = None
    location: str | None = None
    part_no: str | None = None
    product_name: str | None = None


class D1(BaseModel):
    champion: str | None = None
    team_leader: str | None = None
    team_members: str | None = None


class D2(BaseModel):
    problem_statement: str | None = None


class D3(BaseModel):
    ica_description: str | None = None
    ica_effective: str | None = None
    ica_target_date: str | date | None = None
    ica_actual_date: str | date | None = None

    @model_validator(mode="after")
    def serialize_dates(self):
        if isinstance(self.ica_target_date, str):
            self.ica_target_date = excel_serial_to_date(int(self.ica_target_date))
        if isinstance(self.ica_actual_date, str):
            self.ica_actual_date = excel_serial_to_date(int(self.ica_actual_date))
        return self


class D4(BaseModel):
    rc_description: str | None = None
    rc_contribution: int | float | None = None


class D5(BaseModel):
    choose_pca_description: str | None = None
    choose_pca_effectivity: int | float | None = None


class D6(BaseModel):
    implement_pca_description: str | None = None
    implement_pca_target_date: str | date | None = None
    implement_pca_actual_date: str | date | None = None

    @model_validator(mode="after")
    def serialize_dates(self):
        if isinstance(self.implement_pca_target_date, str):
            self.implement_pca_target_date = excel_serial_to_date(
                int(self.implement_pca_target_date)
            )
        if isinstance(self.implement_pca_actual_date, str):
            self.implement_pca_actual_date = excel_serial_to_date(
                int(self.implement_pca_actual_date)
            )
        return self


class D7(BaseModel):
    spa_description: str | None = None
    spa_target_date: str | date | None = None
    spa_actual_date: str | date | None = None
    control_plan: bool = False
    fmea: bool = False
    flowchart: bool = False
    proc_work_instr: bool = False
    add_to_internal_audit: bool = False

    @model_validator(mode="after")
    def serialize_dates(self):
        if isinstance(self.spa_target_date, str):
            self.spa_target_date = excel_serial_to_date(int(self.spa_target_date))
        if isinstance(self.spa_actual_date, str):
            self.spa_actual_date = excel_serial_to_date(int(self.spa_actual_date))
        return self


class DocBody(BaseModel):
    d1: D1 | None = None
    d2: D2 | None = None
    d3: D3 | None = None
    d4: D4 | None = None
    d5: D5 | None = None
    d6: D6 | None = None
    d7: D7 | None = None


class Document(BaseModel):
    doc_meta: DocMeta
    definitions: Definitions
    doc_body: DocBody


class TransformStrategy8DExcelMapper001v1:
    def __init__(self, *, target_format: ContentFormat, data: TransformableData):
        self.target_format = target_format
        self.data = data
        self.parsed_content = json.loads(self.data.content)
        self.refs = self._resolve_coord_refs()
        self.shared_strings = self._resolve_shared_strings()

    def transform(self) -> TransformedData:
        doc_meta = self._build_model(model=DocMeta)
        definitions = self._build_model(model=Definitions)
        doc_body = DocBody(
            d1=self._build_model(model=D1),
            d2=self._build_model(model=D2),
            d3=self._build_model(model=D3),
            d4=self._build_model(model=D4),
            d5=self._build_model(model=D5),
            d6=self._build_model(model=D6),
            d7=self._build_model(model=D7),
        )
        document = Document(
            doc_meta=doc_meta, definitions=definitions, doc_body=doc_body
        )
        doc_bytes = json.dumps(
            document.model_dump(mode="json"), ensure_ascii=False
        ).encode()
        return TransformedData(content=doc_bytes)

    def _build_model(self, *, model: type[M]) -> M:
        result_dict = {}
        for field_name in model.model_fields:  # type: ignore[arg-type]
            checkbox_address = CHECKBOXES.get(field_name)
            if checkbox_address:
                props = self.parsed_content[checkbox_address]["formControlPr"]
                result_dict[field_name] = "@checked" in props
                continue
            coord = COORDS.get(field_name)
            if not coord or not self.refs.get(coord):
                continue
            val_type, val = self.refs[coord]
            result_dict[field_name] = (
                self.shared_strings[int(val)] if val_type == "s" else val
            )
        try:
            return model(**result_dict)
        except ValidationError as e:
            raise errors.TransformError(f"Transform failed: {e}") from e

    def _resolve_coord_refs(self) -> dict:
        refs: dict = {}
        rows = self.parsed_content["xl/worksheets/sheet2.xml"]["worksheet"][
            "sheetData"
        ]["row"]
        for row in rows:
            cells = row.get("c", [])
            if isinstance(cells, dict):
                cells = [cells]
            for cell in cells:
                ref = cell["@r"]
                if ref in COORDS_SET:
                    refs[ref] = (cell.get("@t"), cell.get("v"))
        return refs

    def _resolve_shared_strings(self) -> list:
        raw = self.parsed_content["xl/sharedStrings.xml"]["sst"]["si"]
        if isinstance(raw, dict):
            raw = [raw]
        return [self._resolve_shared_string(item) for item in raw]

    ### --- Serializers
    @staticmethod
    def _resolve_shared_string(item) -> str:
        text = item.get("t") if isinstance(item, dict) else item
        if isinstance(text, dict):
            return text.get("#text", "")
        return text or ""
