import base64
import json
import uuid
from datetime import datetime


def encode_cursor(created_at: datetime, id_: uuid.UUID) -> str:
    payload = {"created_at": created_at.isoformat(), "id": str(id_)}
    raw = json.dumps(payload).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        payload = json.loads(raw)
        return datetime.fromisoformat(payload["created_at"]), uuid.UUID(payload["id"])
    except Exception as exc:
        raise ValueError("Cursor invalid") from exc