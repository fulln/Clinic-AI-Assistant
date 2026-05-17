import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime


class UserRole(str, enum.Enum):
    DOCTOR = "doctor"
    STAFF = "staff"
    ADMIN = "admin"


@dataclass
class User:
    username: str
    password_hash: str
    role: UserRole
    display_name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not self.username or len(self.username) < 3:
            raise ValueError("username must be at least 3 characters")
        if not self.display_name:
            raise ValueError("display_name is required")

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.utcnow()
