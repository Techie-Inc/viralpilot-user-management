from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import logging

from config import Config
from database import init_database, get_db_session
from user_service import UserService
from schemas import (
    UserCreateRequest, UserStatusResponse, UserStatusErrorResponse,
    UserTierUpdateRequest, TokenConsumeRequest, TokenAddRequest,
    UserResponse, HealthResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting User Management Service...")
    Config.validate_config()
    init_database()
    logger.info("User Management Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down User Management Service...")

# Create FastAPI app
app = FastAPI(
    title="Viral Pilot User Management Service",
    description="Service for managing user subscriptions, tokens, and tier information",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=Config.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Viral Pilot User Management Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "user_status": "/user/{cognito_user_id}/status",
            "create_user": "/user",
            "update_tier": "/user/{cognito_user_id}/tier",
            "consume_tokens": "/user/{cognito_user_id}/consume-tokens",
            "add_tokens": "/user/{cognito_user_id}/add-tokens"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        with get_db_session() as session:
            session.execute("SELECT 1")
            db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    return HealthResponse(
        status="healthy",
        service="user-management",
        timestamp=datetime.now().isoformat(),
        database=db_status
    )

@app.post("/user", response_model=UserResponse)
async def create_user(request: UserCreateRequest):
    """Create a new user with default free tier."""
    try:
        with get_db_session() as session:
            user = UserService.create_user(
                session=session,
                cognito_user_id=request.cognito_user_id
            )
            return UserResponse(**user.to_dict())
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/{cognito_user_id}/status", response_model=UserStatusResponse)
async def get_user_status(cognito_user_id: str):
    """Get user's subscription status and token information."""
    try:
        with get_db_session() as session:
            status = UserService.get_user_status(session, cognito_user_id)
            
            if "error" in status:
                raise HTTPException(status_code=404, detail=status["error"])
            
            return UserStatusResponse(**status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/{cognito_user_id}", response_model=UserResponse)
async def get_user(cognito_user_id: str):
    """Get user by Cognito user ID (creates if not exists)."""
    try:
        with get_db_session() as session:
            user = UserService.get_or_create_user(session, cognito_user_id)
            return UserResponse(**user.to_dict())
    except Exception as e:
        logger.error(f"Error getting/creating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/user/{cognito_user_id}/tier", response_model=UserResponse)
async def update_user_tier(cognito_user_id: str, request: UserTierUpdateRequest):
    """Update user's subscription tier."""
    try:
        with get_db_session() as session:
            user = UserService.update_user_tier(
                session=session,
                cognito_user_id=cognito_user_id,
                tier=request.tier,
                renewal_date=request.renewal_date
            )
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            return UserResponse(**user.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user tier: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/user/{cognito_user_id}/consume-tokens", response_model=UserResponse)
async def consume_tokens(cognito_user_id: str, request: TokenConsumeRequest):
    """Consume tokens for a user."""
    try:
        with get_db_session() as session:
            user = UserService.consume_tokens(
                session=session,
                cognito_user_id=cognito_user_id,
                tokens_to_consume=request.tokens_to_consume
            )
            
            if not user:
                raise HTTPException(
                    status_code=400, 
                    detail="Insufficient tokens or user not found"
                )
            
            return UserResponse(**user.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error consuming tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/user/{cognito_user_id}/add-tokens", response_model=UserResponse)
async def add_tokens(cognito_user_id: str, request: TokenAddRequest):
    """Add tokens to user's account."""
    try:
        with get_db_session() as session:
            user = UserService.add_tokens(
                session=session,
                cognito_user_id=cognito_user_id,
                tokens_to_add=request.tokens_to_add
            )
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            return UserResponse(**user.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tiers", response_model=dict)
async def get_subscription_tiers():
    """Get available subscription tiers."""
    return {
        "tiers": Config.SUBSCRIPTION_TIERS,
        "description": "Available subscription tiers and their token allocations"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=Config.SERVICE_HOST,
        port=Config.SERVICE_PORT,
        reload=True
    ) 