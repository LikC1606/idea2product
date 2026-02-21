from config import get_config

if __name__ == "__main__":
    config = get_config()
    print(config.SQLALCHEMY_DATABASE_URI)