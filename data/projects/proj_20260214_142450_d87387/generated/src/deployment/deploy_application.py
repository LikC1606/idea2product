import os
import logging
from src.backend.database_integration import DatabaseManager
from src.ai.content_generation import ContentGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentManager:
    def __init__(self, db_config, ai_model_path):
        self.db_manager = DatabaseManager(db_config)
        self.content_generator = ContentGenerator(ai_model_path)

    def setup_environment(self):
        logger.info("Setting up the production environment...")
        self._check_environment_variables()
        self._initialize_database()
        self._load_ai_model()
        logger.info("Environment setup complete.")

    def _check_environment_variables(self):
        logger.info("Checking environment variables...")
        required_env_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'AI_MODEL_PATH']
        missing_vars = [var for var in required_env_vars if var not in os.environ]

        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("All required environment variables are set.")

    def _initialize_database(self):
        logger.info("Initializing database connection...")
        try:
            self.db_manager.connect()
            logger.info("Database connection successfully initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise

    def _load_ai_model(self):
        logger.info("Loading AI model...")
        try:
            self.content_generator.load_model()
            logger.info("AI model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load AI model: {e}")
            raise

    def deploy_application(self):
        logger.info("Starting application deployment...")
        try:
            self.setup_environment()
            self._start_application_server()
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            raise
        logger.info("Application deployed successfully.")

    def _start_application_server(self):
        logger.info("Starting the application server...")
        try:
            # Simulating starting the application server
            os.system("gunicorn --bind 0.0.0.0:8000 src.app:app")
        except Exception as e:
            logger.error(f"Failed to start the application server: {e}")
            raise

if __name__ == "__main__":
    db_config = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME', 'product_description_db')
    }
    ai_model_path = os.getenv('AI_MODEL_PATH')

    deployment_manager = DeploymentManager(db_config, ai_model_path)
    deployment_manager.deploy_application()