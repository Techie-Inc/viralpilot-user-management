from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, date
from typing import Optional, Dict, Any
from models import UserData
from config import Config
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Service class for user management operations."""
    
    @staticmethod
    def create_user(
        session: Session,
        cognito_user_id: str
    ) -> UserData:
        """Create a new user with default free tier."""
        try:
            user = UserData(
                cognito_user_id=cognito_user_id,
                subscription_tier="free",
                subscription_status="active",
                tokens_remaining=0,
                tokens_used_this_month=0
            )
            
            session.add(user)
            session.commit()
            session.refresh(user)
            
            logger.info(f"Created new user: {cognito_user_id}")
            return user
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error creating user {cognito_user_id}: {e}")
            raise
    
    @staticmethod
    def get_user(session: Session, cognito_user_id: str) -> Optional[UserData]:
        """Get user by Cognito user ID."""
        try:
            return session.query(UserData).filter(
                UserData.cognito_user_id == cognito_user_id,
                UserData.is_active == True
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user {cognito_user_id}: {e}")
            raise
    
    @staticmethod
    def get_or_create_user(
        session: Session,
        cognito_user_id: str
    ) -> UserData:
        """Get user or create if not exists (for legacy users)."""
        user = UserService.get_user(session, cognito_user_id)
        
        if user is None:
            # User doesn't exist, create with free tier
            user = UserService.create_user(session, cognito_user_id)
            logger.info(f"Created legacy user with free tier: {cognito_user_id}")
        
        return user
    
    @staticmethod
    def update_user_tier(
        session: Session,
        cognito_user_id: str,
        tier: str,
        renewal_date: Optional[datetime] = None
    ) -> Optional[UserData]:
        """Update user's subscription tier."""
        try:
            user = UserService.get_user(session, cognito_user_id)
            if not user:
                return None
            
            # Validate tier
            if tier not in Config.SUBSCRIPTION_TIERS:
                raise ValueError(f"Invalid tier: {tier}")
            
            user.subscription_tier = tier
            user.subscription_renewal_date = renewal_date
            
            # Set initial tokens based on tier
            tier_config = Config.SUBSCRIPTION_TIERS[tier]
            if tier_config["tokens_per_month"] >= 0:  # Not unlimited
                user.tokens_remaining = tier_config["tokens_per_month"]
                user.tokens_used_this_month = 0
                user.last_token_reset_date = datetime.now()
            
            session.commit()
            session.refresh(user)
            
            logger.info(f"Updated user {cognito_user_id} to tier: {tier}")
            return user
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating user tier {cognito_user_id}: {e}")
            raise
    
    @staticmethod
    def check_and_reset_tokens(session: Session, cognito_user_id: str) -> Optional[UserData]:
        """Check if tokens need to be reset (monthly for tester tier)."""
        try:
            user = UserService.get_user(session, cognito_user_id)
            if not user:
                return None
            
            # Only reset tokens for tester tier
            if user.subscription_tier == "tester":
                current_date = date.today()
                
                # Check if we need to reset tokens (first day of month)
                if (user.last_token_reset_date is None or 
                    user.last_token_reset_date.date().month != current_date.month or
                    user.last_token_reset_date.date().year != current_date.year):
                    
                    tier_config = Config.SUBSCRIPTION_TIERS[user.subscription_tier]
                    user.tokens_remaining = tier_config["tokens_per_month"]
                    user.tokens_used_this_month = 0
                    user.last_token_reset_date = datetime.now()
                    
                    session.commit()
                    session.refresh(user)
                    
                    logger.info(f"Reset tokens for user {cognito_user_id} to {user.tokens_remaining}")
            
            return user
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error checking/resetting tokens for user {cognito_user_id}: {e}")
            raise
    
    @staticmethod
    def consume_tokens(
        session: Session,
        cognito_user_id: str,
        tokens_to_consume: int = 1
    ) -> Optional[UserData]:
        """Consume tokens for a user."""
        try:
            user = UserService.check_and_reset_tokens(session, cognito_user_id)
            if not user:
                return None
            
            # Check if user has unlimited tokens (admin tier)
            if user.subscription_tier == "admin":
                return user
            
            # Check if user has enough tokens
            if user.tokens_remaining < tokens_to_consume:
                logger.warning(f"User {cognito_user_id} doesn't have enough tokens. Required: {tokens_to_consume}, Available: {user.tokens_remaining}")
                return None
            
            # Consume tokens
            user.tokens_remaining -= tokens_to_consume
            user.tokens_used_this_month += tokens_to_consume
            
            session.commit()
            session.refresh(user)
            
            logger.info(f"Consumed {tokens_to_consume} tokens for user {cognito_user_id}. Remaining: {user.tokens_remaining}")
            return user
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error consuming tokens for user {cognito_user_id}: {e}")
            raise
    
    @staticmethod
    def get_user_status(session: Session, cognito_user_id: str) -> Dict[str, Any]:
        """Get user's subscription status and token information."""
        try:
            user = UserService.check_and_reset_tokens(session, cognito_user_id)
            if not user:
                return {
                    "error": "User not found",
                    "can_make_request": False
                }
            
            tier_config = Config.SUBSCRIPTION_TIERS[user.subscription_tier]
            
            # Determine if user can make requests
            can_make_request = (
                user.subscription_tier == "admin" or  # Admin has unlimited tokens
                user.tokens_remaining > 0  # User has tokens available
            )
            
            return {
                "cognito_user_id": user.cognito_user_id,
                "subscription_tier": user.subscription_tier,
                "subscription_status": user.subscription_status,
                "tokens_remaining": user.tokens_remaining,
                "tokens_used_this_month": user.tokens_used_this_month,
                "subscription_renewal_date": user.subscription_renewal_date.isoformat() if user.subscription_renewal_date else None,
                "can_make_request": can_make_request,
                "tier_name": tier_config["name"],
                "tier_description": tier_config["description"]
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting user status for {cognito_user_id}: {e}")
            raise
    
    @staticmethod
    def add_tokens(
        session: Session,
        cognito_user_id: str,
        tokens_to_add: int
    ) -> Optional[UserData]:
        """Add tokens to user's account (for top-ups)."""
        try:
            user = UserService.get_user(session, cognito_user_id)
            if not user:
                return None
            
            user.tokens_remaining += tokens_to_add
            session.commit()
            session.refresh(user)
            
            logger.info(f"Added {tokens_to_add} tokens to user {cognito_user_id}. Total: {user.tokens_remaining}")
            return user
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error adding tokens for user {cognito_user_id}: {e}")
            raise 