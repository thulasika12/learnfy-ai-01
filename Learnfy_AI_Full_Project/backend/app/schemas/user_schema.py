"""Validated Pydantic schemas for users and authentication."""
import re
from datetime import datetime
from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator

PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,100}$")
NAME_PATTERN = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ' .-]+$")


def validate_strong_password(value: str) -> str:
    if not PASSWORD_PATTERN.match(value):
        raise ValueError("Password must contain uppercase, lowercase, number and special character")
    return value


class RoleEnum(str, Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    confirm_password: str = Field(min_length=8, max_length=100)
    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = " ".join(value.strip().split())
        if not NAME_PATTERN.match(value):
            raise ValueError("Name may contain only letters, spaces, apostrophes, dots and hyphens")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return validate_strong_password(value)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm password do not match")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=100)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    role: RoleEnum
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    academic_level: Optional[str] = None
    academic_stream: Optional[str] = None
    academic_subject: Optional[str] = None
    is_verified_teacher: bool = False
    is_email_verified: bool = False
    onboarding_completed: bool = False
    student_verification_status: str = "unverified"
    student_verified_at: Optional[datetime] = None
    is_active: bool = True
    deleted_at: Optional[datetime] = None
    deletion_reason: Optional[str] = None
    created_at: datetime


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    bio: Optional[str] = Field(default=None, max_length=500)
    academic_level: Optional[Literal["AL"]] = None
    academic_stream: Optional[str] = Field(default=None, max_length=100)
    academic_subject: Optional[str] = Field(default=None, max_length=255)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = " ".join(value.strip().split())
        if not NAME_PATTERN.match(value):
            raise ValueError("Invalid name")
        return value

    @field_validator("bio")
    @classmethod
    def clean_bio(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value is not None else value


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=500)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    reset_token: str = Field(min_length=20, max_length=500)
    new_password: str = Field(min_length=8, max_length=100)
    confirm_password: str = Field(min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return validate_strong_password(value)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=100)
    new_password: str = Field(min_length=8, max_length=100)
    confirm_password: str = Field(min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return validate_strong_password(value)

    @model_validator(mode="after")
    def validate_change(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        if self.current_password == self.new_password:
            raise ValueError("New password must be different from current password")
        return self


class EmailVerificationRequest(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1, max_length=100)

class AdminUserActionRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class OnboardingRequest(BaseModel):
    role: Literal["student", "teacher"]
    education_level_id: int
    grade_id: Optional[int] = None
    stream_id: Optional[int] = None
    medium: Literal["en", "ta", "si"]
    subject_ids: list[int] = Field(min_length=1, max_length=20)
    teacher_grade_ids: list[int] = Field(default_factory=list, max_length=13)
    teacher_subject_ids: list[int] = Field(default_factory=list, max_length=30)
    school_name: Optional[str] = Field(default=None, max_length=255)
    district: Optional[str] = Field(default=None, max_length=100)
    model_config = ConfigDict(extra="forbid")

    @field_validator("school_name", "district")
    @classmethod
    def clean_optional_text(cls, value: Optional[str]) -> Optional[str]:
        value = value.strip() if value else None
        return value or None
