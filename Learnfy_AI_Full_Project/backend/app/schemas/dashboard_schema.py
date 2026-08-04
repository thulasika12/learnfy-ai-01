from pydantic import BaseModel

class DashboardStats(BaseModel):
    uploaded_notes: int = 0
    ai_doubts: int = 0
    quizzes_generated: int = 0
    study_groups: int = 0
