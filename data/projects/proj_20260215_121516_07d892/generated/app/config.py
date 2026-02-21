# app/config.py

class Config:
    """
    Holds application configuration settings for ACM Problem-Solving Platform.
    """
    # General application settings
    APP_NAME = "ACM Problem-Solving Platform"
    VERSION = "1.0.0"
    DEBUG = False

    # Database settings
    DATABASE_URI = "sqlite:///app.db"
    DATABASE_TRACK_MODIFICATIONS = False

    # Security settings
    SECRET_KEY = "your-secret-key"
    SESSION_COOKIE_SECURE = True

    # Features settings
    PROBLEM_LIBRARY_ENABLED = True
    CODE_SUBMISSION_ENABLED = True
    USER_PROFILES_ENABLED = True
    LEADERBOARD_ENABLED = True
    HINTS_AND_TUTORIALS_ENABLED = True

    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    UPLOAD_FOLDER = "uploads/"
    ALLOWED_EXTENSIONS = {"py", "java", "cpp", "txt"}

    # Evaluation settings
    TIME_LIMIT_SECONDS = 2
    MEMORY_LIMIT_MB = 256

    # Leaderboard settings
    LEADERBOARD_UPDATE_INTERVAL = 60  # seconds

    # Email settings for notifications
    EMAIL_NOTIFICATIONS_ENABLED = False
    EMAIL_SERVER = "smtp.example.com"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_USERNAME = "your-email@example.com"
    EMAIL_PASSWORD = "your-email-password"

    # Logging settings
    LOG_FILE = "app/logs/platform.log"
    LOG_LEVEL = "INFO"

    @staticmethod
    def is_extension_allowed(extension):
        """Check if a file extension is allowed for upload."""
        return extension.lower() in Config.ALLOWED_EXTENSIONS