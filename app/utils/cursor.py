import base64
from datetime import datetime

def encode_cursor(created_at: datetime, id_: int) -> str:
    s = f"{created_at.isoformat()}|{id_}"
    return base64.urlsafe_b64encode(s.encode()).decode()

def decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        ts_str, id_ = raw.split("|", 1)
        return datetime.fromisoformat(ts_str), id_
    except Exception:
        raise ValueError("Invalid cursor")