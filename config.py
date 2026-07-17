import os

class Config:
    # SendGrid Configuration
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL", "wonderfulsirjohn@gmail.com")
    
    # SMTP Configuration (Backup - Sio lazima tena)
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    
    # App Configuration
    APP_NAME = "Sales System"
    APP_URL = os.environ.get("APP_URL", "https://sales-system-1-2sq8.onrender.com")
    
    @classmethod
    def is_email_enabled(cls):
        return bool(cls.SENDGRID_API_KEY)