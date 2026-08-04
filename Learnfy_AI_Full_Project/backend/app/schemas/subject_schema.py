from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

STREAMS = ["Biological Science", "Physical Science", "Commerce", "Arts", "Engineering Technology", "Bio Systems Technology", "General/Common Subjects", "General"]

class SubjectWrite(BaseModel):
    level: str = Field(default="AL", pattern="^(PRIMARY|JUNIOR|OL|AL|UNIVERSITY|SELF)$")
    stream: str
    streams: list[str] = Field(default_factory=list)
    subject_code: str = Field(min_length=1, max_length=10, pattern=r"^[A-Z0-9][A-Z0-9-]{0,9}$")
    name_en: str = Field(min_length=2, max_length=255)
    name_ta: str = Field(min_length=2, max_length=255)
    name_si: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0, le=10000)

    @field_validator("stream")
    @classmethod
    def valid_stream(cls, value):
        value = value.strip()
        if not value or len(value) > 100: raise ValueError("A valid stream or category is required")
        return value

    @field_validator("streams")
    @classmethod
    def valid_streams(cls, value):
        cleaned = [item.strip() for item in value if item.strip()]
        if any(len(item) > 100 for item in cleaned): raise ValueError("Invalid stream or category")
        return list(dict.fromkeys(cleaned))

class SubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    level: str
    stream: str
    streams: list[str] = Field(default_factory=list)
    subject_code: str
    name_en: str
    name_ta: str
    name_si: str
    description: str | None
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime
