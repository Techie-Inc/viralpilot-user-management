from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

Base = declarative_base()

class UserData(Base):
    """User data model for storing subscription and token information."""
    
    __tablename__ = "userdata"
    # Using public schema (default)
    
    # Primary key - Cognito User ID
    cognito_user_id = Column(String(255), primary_key=True, nullable=False)
    
    # Subscription information
    subscription_tier = Column(String(50), nullable=False, default="free")
    subscription_status = Column(String(50), nullable=False, default="active")
    subscription_renewal_date = Column(DateTime, nullable=True)
    
    # Token information
    tokens_remaining = Column(Integer, nullable=False, default=0)
    tokens_used_this_month = Column(Integer, nullable=False, default=0)
    last_token_reset_date = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, nullable=False, default=True)
    
    def __repr__(self):
        return f"<UserData(cognito_user_id='{self.cognito_user_id}', tier='{self.subscription_tier}', tokens={self.tokens_remaining})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "cognito_user_id": self.cognito_user_id,
            "subscription_tier": self.subscription_tier,
            "subscription_status": self.subscription_status,
            "subscription_renewal_date": self.subscription_renewal_date.isoformat() if self.subscription_renewal_date else None,
            "tokens_remaining": self.tokens_remaining,
            "tokens_used_this_month": self.tokens_used_this_month,
            "last_token_reset_date": self.last_token_reset_date.isoformat() if self.last_token_reset_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active
        } 