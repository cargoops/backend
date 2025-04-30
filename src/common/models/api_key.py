from datetime import datetime
import uuid
from typing import List, Optional
from pydantic import BaseModel

class Permission(BaseModel):
    name: str
    description: str

class APIKey(BaseModel):
    id: str = str(uuid.uuid4())
    key: str = str(uuid.uuid4())
    name: str
    permissions: List[str]
    created_at: datetime = datetime.utcnow()
    expires_at: Optional[datetime] = None
    is_active: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Test API Key",
                "permissions": ["read:packages", "write:packages"],
                "expires_at": "2024-12-31T23:59:59"
            }
        } 