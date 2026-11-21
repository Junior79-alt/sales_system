import os


class Config:
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL", "noreply@example.com")

    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

    APP_NAME = "Sales System"
    APP_URL = os.environ.get("APP_URL", "https://sales-system.onrender.com")

    @classmethod
    def is_email_enabled(cls):
        return bool(cls.SENDGRID_API_KEY)