class Config:
    """Base configuration class for the ACM Problem-Solving Platform."""

    # General Configurations
    SECRET_KEY = "your-secret-key"
    DEBUG = False
    TESTING = False

    # Database Configurations
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Application Features
    ENABLE_LEADERBOARD = True
    ENABLE_HINTS_AND_TUTORIALS = True

    # Other Configurations
    PER_PAGE = 10
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit for submissions


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///dev.db"


class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "postgresql://user:password@localhost/prod_db"