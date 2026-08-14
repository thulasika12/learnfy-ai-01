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
    STORAGE_BACKEND: str = "local"
    AWS_ENDPOINT_URL: str = ""
    AWS_S3_BUCKET_NAME: str = ""
    AWS_DEFAULT_REGION: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    PRIVATE_URL_EXPIRE_SECONDS: int = 900
    UPLOAD_QUOTA_MB_PER_USER: int = 250
    ANTIVIRUS_ENABLED: bool = False
    ANTIVIRUS_REQUIRED: bool = False
    CLAMAV_HOST: str = ""
    REDIS_URL: str = ""
    TRUST_PROXY_HEADERS: bool = False

    # Google Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Resend HTTPS email delivery
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "onboarding@resend.dev"

    # Stripe (server-side only; never expose these secrets to the frontend)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    PAYMENTS_ENABLED: bool = False
    PAYMENT_PROVIDER: str = "payhere"
    STRIPE_MONTHLY_PRICE_ID: str = ""
    STRIPE_YEARLY_PRICE_ID: str = ""
    STRIPE_PORTAL_RETURN_URL: str = ""
    PAYHERE_ENABLED: bool = False
    PAYHERE_SANDBOX: bool = True
    PAYHERE_MERCHANT_ID: str = ""
    PAYHERE_MERCHANT_SECRET: str = ""
    PAYHERE_CURRENCY: str = "LKR"
    PAYHERE_30_DAY_AMOUNT: str = "500.00"
    PAYHERE_365_DAY_AMOUNT: str = "5000.00"
    FREE_AI_CHAT_LIMIT: int = 5
    FREE_SUMMARY_LIMIT: int = 3
    FREE_QUIZ_LIMIT: int = 2
    FREE_FLASHCARDS_LIMIT: int = 2
    FREE_STUDY_PLANNER_LIMIT: int = 5
    PREMIUM_AI_CHAT_LIMIT: int = 100
    PREMIUM_SUMMARY_LIMIT: int = 50
    PREMIUM_QUIZ_LIMIT: int = 30
    PREMIUM_FLASHCARDS_LIMIT: int = 30
    PREMIUM_STUDY_PLANNER_LIMIT: int = 20
    PDF_UNICODE_FONT_PATH: str = ""

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.ENVIRONMENT.lower() == "production":
            if len(self.JWT_SECRET_KEY) < 32 or self.JWT_SECRET_KEY.lower().startswith(("change", "insecure")):
                raise ValueError("JWT_SECRET_KEY must be a strong configured secret in production")
            if "YOUR_PASSWORD" in self.DATABASE_URL or "root:password@" in self.DATABASE_URL:
                raise ValueError("DATABASE_URL must be configured in production")
            if self.STORAGE_BACKEND != "s3":
                raise ValueError("STORAGE_BACKEND=s3 is required in production")
            if not all((self.AWS_ENDPOINT_URL, self.AWS_S3_BUCKET_NAME, self.AWS_DEFAULT_REGION,
                        self.AWS_ACCESS_KEY_ID, self.AWS_SECRET_ACCESS_KEY)):
                raise ValueError("Railway S3 bucket settings must be configured in production")
            if not self.REDIS_URL:
                raise ValueError("REDIS_URL is required in production")
            if self.PAYMENTS_ENABLED:
                required = (self.STRIPE_SECRET_KEY, self.STRIPE_WEBHOOK_SECRET,
                            self.STRIPE_MONTHLY_PRICE_ID, self.STRIPE_YEARLY_PRICE_ID)
                if self.PAYMENT_PROVIDER != "stripe" or not all(required):
                    raise ValueError("Enabled Stripe payments require provider, secrets, and both Price IDs")
            if self.PAYHERE_ENABLED:
                if self.PAYMENT_PROVIDER != "payhere":
                    raise ValueError("PAYMENT_PROVIDER must be payhere when PayHere is enabled")
                if not self.PAYHERE_MERCHANT_ID or not self.PAYHERE_MERCHANT_SECRET:
                    raise ValueError("Enabled PayHere requires merchant ID and merchant secret")
                if not self.BACKEND_PUBLIC_URL.lower().startswith("https://"):
                    raise ValueError("Enabled PayHere requires an HTTPS BACKEND_PUBLIC_URL")
                if not self.PAYHERE_SANDBOX and not self.FRONTEND_URL.lower().startswith("https://"):
                    raise ValueError("PayHere Production requires an HTTPS FRONTEND_URL")
                if self.PAYHERE_CURRENCY.upper() != "LKR":
                    raise ValueError("Learnfy AI PayHere payments must use LKR")
            if self.ANTIVIRUS_REQUIRED and not self.ANTIVIRUS_ENABLED:
                raise ValueError("ANTIVIRUS_ENABLED must be true when ANTIVIRUS_REQUIRED is true")
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
        return origins


settings = Settings()
