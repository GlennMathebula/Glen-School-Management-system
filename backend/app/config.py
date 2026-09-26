from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):

    # ========================================================
    # DATABASE
    # ========================================================

    database_url: str

    # ========================================================
    # EMAIL
    # ========================================================

    mail_host: str

    mail_port: int = 587

    mail_username: str

    mail_password: str

    mail_from: str

    mail_from_name: str = (
        "Glen Moniques"
    )

    # ========================================================
    # JWT
    # ========================================================

    jwt_secret_key: str

    jwt_access_token_expire_minutes: int = 60

    jwt_refresh_token_expire_minutes: int = 1440

    # ========================================================
    # SUPABASE STORAGE
    # ========================================================

    supabase_url: str

    supabase_service_role_key: str

    # ========================================================
    # SETTINGS
    # ========================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    # ========================================================
    # PAYFAST
    # ========================================================

    payfast_merchant_id: str | None = None
    payfast_merchant_key: str | None = None
    payfast_passphrase: str | None = None

    payfast_sandbox: bool = True

    payfast_return_url: str = (
        "http://127.0.0.1:8000/api/payments/payfast/return"
    )

    payfast_cancel_url: str = (
        "http://127.0.0.1:8000/api/payments/payfast/cancel"
    )

    payfast_notify_url: str = (
        "http://127.0.0.1:8000/api/payments/payfast/notify"
    )

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None

    smtp_from_email: str = "glenmoniquesptyltd@gmail.com"
    smtp_from_name: str = "Glen Moniques"

    smtp_use_tls: bool = True


settings = Settings()