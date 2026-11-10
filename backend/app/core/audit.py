
from sqlalchemy.orm import Session

from data_engineering.storage.models import AuditLog


def record_audit(
    db: Session,
    action: str,
    resource_type: str,
    user_id: str | None = None,
    project_id: str | None = None,
    resource_id: str | None = None,
    details: dict | None = None,
) -> AuditLog:
    """
    Add an audit event to the current database transaction.

    The caller is responsible for committing or rolling back
    the transaction. Sensitive credentials must never be stored.
    """

    audit_entry = AuditLog(
        user_id=user_id,
        project_id=project_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
    )

    db.add(audit_entry)

    return audit_entry
