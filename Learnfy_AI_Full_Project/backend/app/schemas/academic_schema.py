from pydantic import BaseModel, ConfigDict, Field

class LocalizedAcademicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; code: str; name_en: str; name_ta: str; name_si: str; sort_order: int; is_active: bool

class GradeOut(LocalizedAcademicOut):
    level_id: int; grade_number: int | None = None

class AcademicProfileWrite(BaseModel):
    education_level_id: int | None = None; grade_id: int | None = None; stream_id: int | None = None
    medium: str | None = Field(default=None, pattern="^(en|ta|si)$")
    subject_ids: list[int] = Field(default_factory=list, max_length=20)
    teacher_grade_ids: list[int] = Field(default_factory=list, max_length=13)
    teacher_subject_ids: list[int] = Field(default_factory=list, max_length=30)
    school_name: str | None = Field(default=None, max_length=255); district: str | None = Field(default=None, max_length=100)
    guardian_consent: bool = False

class AcademicProfileOut(BaseModel):
    education_level_id: int | None = None; grade_id: int | None = None; stream_id: int | None = None
    medium: str | None = None; school_name: str | None = None; district: str | None = None; guardian_consent: bool = False
    subject_ids: list[int] = Field(default_factory=list); teacher_grade_ids: list[int] = Field(default_factory=list); teacher_subject_ids: list[int] = Field(default_factory=list)
