import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the User Management Service."""
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:lac005Pzlooqo1rYObjX@r2r-db.c5ocg6qw2d94.af-south-1.rds.amazonaws.com:5432/postgres")
    
    # Service Configuration
    SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")
    SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8001"))
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    
    # Subscription Tiers Configuration
    SUBSCRIPTION_TIERS = {
        "admin": {
            "name": "Admin",
            "tokens_per_month": -1,  # -1 means unlimited
            "description": "Administrator tier with unlimited tokens"
        },
        "tester": {
            "name": "Tester",
            "tokens_per_month": 1000,
            "description": "Tester tier with 1000 tokens per month"
        },
        "free": {
            "name": "Free",
            "tokens_per_month": 0,
            "description": "Free tier with no tokens"
        },
        "basic": {
            "name": "Basic",
            "tokens_per_month": 0,  # To be defined later
            "description": "Basic tier (to be defined)"
        },
        "creator": {
            "name": "Creator",
            "tokens_per_month": 0,  # To be defined later
            "description": "Creator tier (to be defined)"
        },
        "agency": {
            "name": "Agency",
            "tokens_per_month": 0,  # To be defined later
            "description": "Agency tier (to be defined)"
        }
    }
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present."""
        required_vars = ["DATABASE_URL"]
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required configuration variables: {missing_vars}")
        
        # Validate DATABASE_URL format
        if not cls.DATABASE_URL.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL connection string") 