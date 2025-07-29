"""
Integration Example for PostPilot Backend

This file shows how the PostPilot backend should integrate with the User Management Service
to check user permissions and consume tokens before making LLM requests.
"""

import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class UserManagementIntegration:
    """Integration class for User Management Service."""
    
    def __init__(self, user_management_url: str = "http://localhost:8001"):
        self.user_management_url = user_management_url.rstrip('/')
    
    def check_user_permission(self, cognito_user_id: str) -> Dict[str, Any]:
        """
        Check if user can make LLM requests.
        
        Args:
            cognito_user_id: The Cognito User ID
            
        Returns:
            User status information
            
        Raises:
            Exception: If user cannot make requests or service is unavailable
        """
        try:
            response = requests.get(
                f"{self.user_management_url}/user/{cognito_user_id}/status",
                timeout=10
            )
            
            if response.status_code == 200:
                user_status = response.json()
                
                if not user_status["can_make_request"]:
                    if user_status["subscription_tier"] == "free":
                        raise Exception("Please subscribe to a plan to use this feature")
                    else:
                        raise Exception("Please top up your account with tokens")
                
                return user_status
            else:
                raise Exception(f"Failed to check user status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"User management service request failed: {e}")
            raise Exception("User management service is unavailable")
    
    def consume_user_tokens(self, cognito_user_id: str, tokens_consumed: int = 1) -> bool:
        """
        Consume tokens after successful LLM request.
        
        Args:
            cognito_user_id: The Cognito User ID
            tokens_consumed: Number of tokens to consume (default: 1)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.user_management_url}/user/{cognito_user_id}/consume-tokens",
                json={"tokens_to_consume": tokens_consumed},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully consumed {tokens_consumed} tokens for user {cognito_user_id}")
                return True
            else:
                logger.warning(f"Failed to consume tokens for user {cognito_user_id}: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to consume tokens for user {cognito_user_id}: {e}")
            return False
    
    def get_or_create_user(self, cognito_user_id: str) -> Dict[str, Any]:
        """
        Get user or create if not exists (for legacy users).
        
        Args:
            cognito_user_id: The Cognito User ID
            
        Returns:
            User information
        """
        try:
            response = requests.get(
                f"{self.user_management_url}/user/{cognito_user_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to get/create user: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get/create user {cognito_user_id}: {e}")
            raise Exception("User management service is unavailable")

# Example usage in PostPilot backend
def example_llm_request_with_user_check(cognito_user_id: str, user_input: str):
    """
    Example of how to integrate user management with LLM requests in PostPilot backend.
    """
    # Initialize integration
    user_mgmt = UserManagementIntegration()
    
    try:
        # Step 1: Check user permission before making LLM request
        user_status = user_mgmt.check_user_permission(cognito_user_id)
        logger.info(f"User {cognito_user_id} has {user_status['tokens_remaining']} tokens remaining")
        
        # Step 2: Make LLM request (your existing OpenAI service call)
        # llm_response = openai_service.generate_viral_content(...)
        # For this example, we'll simulate a successful LLM request
        llm_response = {"success": True, "tokens_used": 1}
        
        # Step 3: Consume tokens after successful LLM request
        if llm_response["success"]:
            tokens_consumed = llm_response.get("tokens_used", 1)
            user_mgmt.consume_user_tokens(cognito_user_id, tokens_consumed)
        
        return llm_response
        
    except Exception as e:
        logger.error(f"Error in LLM request for user {cognito_user_id}: {e}")
        # Handle the error appropriately (show popup, return error response, etc.)
        raise

# Example of handling different user scenarios
def handle_user_scenarios():
    """Example of handling different user scenarios."""
    user_mgmt = UserManagementIntegration()
    
    # Scenario 1: Free user trying to make request
    try:
        user_mgmt.check_user_permission("free-user-123")
    except Exception as e:
        if "subscribe to a plan" in str(e):
            # Show subscription popup
            print("Show subscription popup to user")
    
    # Scenario 2: Tester user with tokens
    try:
        user_status = user_mgmt.check_user_permission("tester-user-456")
        print(f"Tester user can make request. Tokens remaining: {user_status['tokens_remaining']}")
    except Exception as e:
        print(f"Tester user error: {e}")
    
    # Scenario 3: Admin user (unlimited tokens)
    try:
        user_status = user_mgmt.check_user_permission("admin-user-789")
        print(f"Admin user can make unlimited requests. Tier: {user_status['subscription_tier']}")
    except Exception as e:
        print(f"Admin user error: {e}")

if __name__ == "__main__":
    # Run example scenarios
    handle_user_scenarios() 