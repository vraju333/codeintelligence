import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME = os.getenv("APP_NAME", "CodeIntelligence")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
    DATABASE_URL = os.getenv("DATABASE_URL")
    JAVA_PROJECT_PATH = os.getenv("JAVA_PROJECT_PATH")


settings = Settings()
