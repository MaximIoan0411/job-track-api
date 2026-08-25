import enum


class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    PHONE_SCREEN = "phone_screen"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class AuditAction(str, enum.Enum):
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    UPDATED = "updated"
    SOFT_DELETED = "soft_deleted"
    RESTORED = "restored"