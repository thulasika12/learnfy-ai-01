from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field

class TeacherVerificationOut(BaseModel):
    id: int; user_id: int; full_name: str; qualification: str | None = None; institution_name: str
    subjects_taught: list[str]; grades_taught: list[str]; years_of_experience: int
    official_email: EmailStr | None = None; additional_information: str | None = None
    status: Literal["pending", "approved", "rejected"]; rejection_reason: str | None = None
    submitted_at: datetime; reviewed_at: datetime | None = None; reviewed_by: int | None = None
    has_proof: bool = True
    applicant_email: EmailStr | None = None

class RejectionRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)
