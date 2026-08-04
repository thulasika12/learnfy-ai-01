"""
Application configuration loaded from environment variables (.env file).
Uses pydantic-settings so values are validated and typed.
"""
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Learnfy AI"
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    UPLOAD_DIR: str = "app/uploads"
    TEACHER_VERIFICATION_DIR: str = "app/private/teacher-verifications"
    TEACHER_VERIFICATION_MAX_MB: int = 5
    STUDENT_VERIFICATION_DIR: str = "app/private/student-verifications"
    STUDENT_VERIFICATION_MAX_MB: int = 5
    BACKEND_PUBLIC_URL: str = "http://localhost:8000"

    # Database
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/learnfy_ai"

    # JWT
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    MAX_UPLOAD_SIZE_MB: int = 20

    # Google Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Optional SMTP email delivery
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True

    # Stripe (server-side only; never expose these secrets to the frontend)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    PDF_UNICODE_FONT_PATH: str = ""

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.ENVIRONMENT.lower() == "production":
            if len(self.JWT_SECRET_KEY) < 32 or self.JWT_SECRET_KEY.lower().startswith(("change", "insecure")):
                raise ValueError("JWT_SECRET_KEY must be a strong configured secret in production")
            if "YOUR_PASSWORD" in self.DATABASE_URL or "root:password@" in self.DATABASE_URL:
                raise ValueError("DATABASE_URL must be configured in production")
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
        return origins


settings = Settings()
