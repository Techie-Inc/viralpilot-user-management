from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserCreateRequest(BaseModel):
    """Request schema for creating a new user."""
    cognito_user_id: str = Field(..., description="Cognito User ID")

class UserStatusResponse(BaseModel):
    """Response schema for user status."""
    cognito_user_id: str
    subscription_tier: str
    subscription_status: str
    tokens_remaining: int
    tokens_used_this_month: int
    subscription_renewal_date: Optional[str] = None
    can_make_request: bool
    tier_name: str
    tier_description: str

class UserStatusErrorResponse(BaseModel):
    """Error response schema for user status."""
    error: str
    can_make_request: bool = False

class UserTierUpdateRequest(BaseModel):
    """Request schema for updating user tier."""
    tier: str = Field(..., description="Subscription tier")
    renewal_date: Optional[datetime] = Field(None, description="Subscription renewal date")

class TokenConsumeRequest(BaseModel):
    """Request schema for consuming tokens."""
    tokens_to_consume: int = Field(1, ge=1, description="Number of tokens to consume")

class TokenAddRequest(BaseModel):
    """Request schema for adding tokens."""
    tokens_to_add: int = Field(..., gt=0, description="Number of tokens to add")

class UserResponse(BaseModel):
    """Response schema for user data."""
    cognito_user_id: str
    subscription_tier: str
    subscription_status: str
    tokens_remaining: int
    tokens_used_this_month: int
    subscription_renewal_date: Optional[str]
    last_token_reset_date: Optional[str]
    created_at: str
    updated_at: str
    is_active: bool

class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    service: str
    timestamp: str
    database: str 