from sqlalchemy.orm import Session
from fastapi import Request
import models


def log_action(
    db: Session,
    user_id: int | None,
    action: str,
    details: str = "",
    request: Request | None = None,
) -> None:
    """Log user action for audit purposes."""
    try:
        ip = request.client.host if request and request.client else "unknown"
        ua = request.headers.get("user-agent", "")[:200] if request else ""

        log = models.AuditLog(
            user_id=user_id,
            action=action,
            details=details[:500],
            ip_address=ip,
            user_agent=ua,
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"⚠️ Audit log error: {e}")