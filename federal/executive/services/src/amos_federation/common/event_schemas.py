"""
AMOS-Federation Event Schema Validation
الهدف: تحميل والتحقق من مخططات أحداث سجل الحوكمة
النطاق: ناشرو ومستهلكو أحداث AMOS-Federation
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import json
from pathlib import Path
from typing import Any


def _schema_directory() -> Path:
    """تحديد دليل السجل من جذر المستودع دون افتراض دليل العمل الحالي."""
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "governance" / "schema-registry"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("تعذر العثور على governance/schema-registry")


def load_event_schema(event_type: str) -> dict[str, Any]:
    """تحميل مخطط JSON المقابل لنوع حدث معلوم."""
    schema_path = _schema_directory() / f"{event_type}.schema.json"
    with schema_path.open(encoding="utf-8") as schema_file:
        return json.load(schema_file)


def _has_required_fields(schema: dict[str, Any], value: Any) -> bool:
    """فحص خفيف للحقول المطلوبة، صالح عند عدم توفير مكتبة jsonschema."""
    if not isinstance(value, dict):
        return False
    if any(field not in value for field in schema.get("required", [])):
        return False
    for field, field_schema in schema.get("properties", {}).items():
        if field in value:
            if "const" in field_schema and value[field] != field_schema["const"]:
                return False
            if "enum" in field_schema and value[field] not in field_schema["enum"]:
                return False
            if field_schema.get("type") == "object" and not _has_required_fields(
                field_schema, value[field]
            ):
                return False
    return True


def validate_event(event_type: str, payload: dict[str, Any]) -> bool:
    """التحقق من حدث؛ يستخدم jsonschema عند توفره ثم فحصًا خفيفًا آمنًا خلاف ذلك."""
    try:
        schema = load_event_schema(event_type)
    except (FileNotFoundError, json.JSONDecodeError):
        return False
    try:
        import jsonschema
    except ImportError:
        return _has_required_fields(schema, payload)
    try:
        jsonschema.validate(instance=payload, schema=schema)
    except jsonschema.ValidationError:
        return False
    return True
