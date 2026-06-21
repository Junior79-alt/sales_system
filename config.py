import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # SendGrid Configuration
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "wonderfulsirjohn@gmail.com")
    
    # App Configuration
    APP_NAME = "Sales System"
    APP_URL = os.getenv("APP_URL", "http://localhost:8081")
    
    @classmethod
    def is_email_enabled(cls):
        return bool(cls.SENDGRID_API_KEY)