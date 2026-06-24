import os

class Config:
    # Soma moja kwa moja kutoka environment variables
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL", "wonderfulsirjohn@gmail.com")
    APP_NAME = "Sales System"
    APP_URL = os.environ.get("APP_URL", "https://sales-system-4.onrender.com")
    
    @classmethod
    def is_email_enabled(cls):
        return bool(cls.SENDGRID_API_KEY)