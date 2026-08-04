"""Small helper for consistent immutable admin audit entries."""
from sqlalchemy.orm import Session

from app.models.admin_audit import AdminAudit


def add_admin_audit(
    db: Session,
    admin_id: int,
    action: str,
    target_type: str,
    target_id: int | None,
    description: str | None = None,
) -> None:
    db.add(AdminAudit(
        actor_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=(description or "")[:4000] or None,
    ))
