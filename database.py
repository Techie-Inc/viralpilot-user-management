from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(Config.DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_database_if_not_exists():
    """Create the viralpilot database if it doesn't exist."""
    try:
        # Connect to the default postgres database to create viralpilot database
        postgres_url = Config.DATABASE_URL.replace('/viralpilot', '/postgres')
        postgres_engine = create_engine(postgres_url, echo=False)
        
        with postgres_engine.connect() as connection:
            # Check if viralpilot database exists
            result = connection.execute(text("SELECT 1 FROM pg_database WHERE datname = 'viralpilot'"))
            if not result.fetchone():
                # Create viralpilot database
                connection.execute(text("CREATE DATABASE viralpilot"))
                connection.commit()
                logger.info("Created viralpilot database")
            else:
                logger.info("viralpilot database already exists")
                
    except SQLAlchemyError as e:
        logger.error(f"Error creating database: {e}")
        raise

def create_schema_and_tables():
    """Create the userdata table in the public schema if it doesn't exist."""
    try:
        with engine.connect() as connection:
            # Create table if it doesn't exist (using public schema)
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS userdata (
                cognito_user_id VARCHAR(255) PRIMARY KEY NOT NULL,
                subscription_tier VARCHAR(50) NOT NULL DEFAULT 'free',
                subscription_status VARCHAR(50) NOT NULL DEFAULT 'active',
                subscription_renewal_date TIMESTAMP,
                tokens_remaining INTEGER NOT NULL DEFAULT 0,
                tokens_used_this_month INTEGER NOT NULL DEFAULT 0,
                last_token_reset_date TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
            """
            connection.execute(text(create_table_sql))
            connection.commit()
            
            logger.info("Database table created successfully")
            
    except SQLAlchemyError as e:
        logger.error(f"Error creating database table: {e}")
        raise

@contextmanager
def get_db_session():
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

def init_database():
    """Initialize the database with schema and tables."""
    logger.info("Initializing database...")
    create_database_if_not_exists()
    create_schema_and_tables()
    logger.info("Database initialization completed") 