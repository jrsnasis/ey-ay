# ey-ay/config/settings.py

import os
from pathlib import Path
from dotenv import load_dotenv

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Load .env file
env_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=env_path)


class DatabaseConfig:
    HOST = os.getenv("DB_HOST", "localhost")
    PORT = int(os.getenv("DB_PORT", 3306))
    NAME = os.getenv("DB_NAME", "chatbot_db")
    USER = os.getenv("DB_USER", "chatbot_user")
    PASSWORD = os.getenv("DB_PASSWORD", "")

    # Connection pool settings
    POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 5))
    MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 10))
    POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", 30))
    POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", 3600))

    @classmethod
    def get_connection_url(cls):
        return f"mysql+pymysql://{cls.USER}:{cls.PASSWORD}@{cls.HOST}:{cls.PORT}/{cls.NAME}?charset=utf8mb4"

    @classmethod
    def get_connection_params(cls):
        return {
            "host": cls.HOST,
            "port": cls.PORT,
            "user": cls.USER,
            "password": cls.PASSWORD,
            "database": cls.NAME,
            "charset": "utf8mb4",
            "use_unicode": True,
            "autocommit": False,
        }


class AppConfig:
    ENV = os.getenv("APP_ENV", "development")
    HOST = os.getenv("APP_HOST", "localhost")
    PORT = int(os.getenv("APP_PORT", 5000))
    DEBUG = ENV == "development"

    # Paths
    PROJECT_ROOT = PROJECT_ROOT
    DATA_DIR = PROJECT_ROOT / "data"
    LOGS_DIR = PROJECT_ROOT / "logs"
    MODELS_DIR = PROJECT_ROOT / "models"

    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
        (cls.DATA_DIR / "processed").mkdir(exist_ok=True)


class LoggingConfig:
    LEVEL = os.getenv("LOG_LEVEL", "INFO")
    FILE = os.getenv("LOG_FILE", "logs/app.log")

    # Detailed format for files
    FILE_FORMAT = (
        "%(asctime)s | %(name)-25s | %(levelname)-8s | %(funcName)-20s | %(message)s"
    )

    # Simpler format for console
    CONSOLE_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"

    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class ModelConfig:
    MODEL_PATH = os.getenv("MODEL_PATH", "data/processed/chatbot_model.pth")
    INTENTS_PATH = os.getenv("INTENTS_PATH", "data/intents.json")
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.75))

    # Training parameters
    HIDDEN_SIZE = int(os.getenv("HIDDEN_SIZE", 8))
    NUM_EPOCHS = int(os.getenv("NUM_EPOCHS", 1000))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", 8))
    LEARNING_RATE = float(os.getenv("LEARNING_RATE", 0.001))


# Validate required environment variables
def validate_config():
    required_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]

    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please create a .env file based on .env.example"
        )


# Run validation on import
if os.getenv("SKIP_CONFIG_VALIDATION") != "true":
    try:
        validate_config()
    except EnvironmentError as e:
        print(f"Configuration Warning: {e}")


# Create directories on import
AppConfig.ensure_directories()
