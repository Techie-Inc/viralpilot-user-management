# Viral Pilot User Management Service

A FastAPI service for managing user subscriptions, tokens, and tier information for the Viral Pilot platform.

## Features

- **User Management**: CRUD operations for user data
- **Subscription Tiers**: Support for admin, tester, free, basic, creator, and agency tiers
- **Token Management**: Track and manage user tokens with monthly resets
- **Database Integration**: PostgreSQL with automatic schema creation
- **RESTful API**: Complete API for user management operations
- **Docker Support**: Containerized deployment

## Subscription Tiers

| Tier | Tokens/Month | Description |
|------|-------------|-------------|
| Admin | Unlimited | Administrator tier with unlimited tokens |
| Tester | 1000 | Tester tier with 1000 tokens per month (resets on 1st) |
| Free | 0 | Free tier with no tokens |
| Basic | TBD | Basic tier (to be defined) |
| Creator | TBD | Creator tier (to be defined) |
| Agency | TBD | Agency tier (to be defined) |

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Docker (optional)

### Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:lac005Pzlooqo1rYObjX@r2r-db.c5ocg6qw2d94.af-south-1.rds.amazonaws.com:5432/postgres

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8001

# CORS Configuration
CORS_ORIGINS=*
CORS_ALLOW_CREDENTIALS=true
```

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the service**:
   ```bash
   python main.py
   ```

3. **Access the API**:
   - API: http://localhost:8001
   - Documentation: http://localhost:8001/docs
   - Health Check: http://localhost:8001/health

### Docker Deployment

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **Or build and run manually**:
   ```bash
   docker build -t viralpilot-user-management .
   docker run -p 8001:8001 --env-file .env viralpilot-user-management
   ```

## API Endpoints

### Health Check
- `GET /health` - Service health check

### User Management
- `POST /user` - Create a new user
- `GET /user/{cognito_user_id}` - Get user (creates if not exists)
- `GET /user/{cognito_user_id}/status` - Get user subscription status
- `PUT /user/{cognito_user_id}/tier` - Update user subscription tier
- `POST /user/{cognito_user_id}/consume-tokens` - Consume tokens
- `POST /user/{cognito_user_id}/add-tokens` - Add tokens to account

### Information
- `GET /tiers` - Get available subscription tiers

## Integration with PostPilot Backend

The PostPilot backend should call the user management service before making LLM requests:

1. **Check user status**: Call `GET /user/{cognito_user_id}/status`
2. **Verify tokens**: Check if `can_make_request` is true
3. **Consume tokens**: Call `POST /user/{cognito_user_id}/consume-tokens` after successful LLM request

### Example Integration Flow

```python
# In PostPilot backend
import requests

def check_user_permission(cognito_user_id: str):
    """Check if user can make LLM requests."""
    response = requests.get(f"http://user-management:8001/user/{cognito_user_id}/status")
    
    if response.status_code == 200:
        user_status = response.json()
        
        if not user_status["can_make_request"]:
            if user_status["subscription_tier"] == "free":
                # Show subscription popup
                raise Exception("Please subscribe to a plan to use this feature")
            else:
                # Show token top-up popup
                raise Exception("Please top up your account with tokens")
        
        return user_status
    else:
        raise Exception("Failed to check user status")

def consume_user_tokens(cognito_user_id: str, tokens_consumed: int = 1):
    """Consume tokens after successful LLM request."""
    response = requests.post(
        f"http://user-management:8001/user/{cognito_user_id}/consume-tokens",
        json={"tokens_to_consume": tokens_consumed}
    )
    
    if response.status_code != 200:
        logger.warning(f"Failed to consume tokens for user {cognito_user_id}")
```

## Database Schema

The service automatically creates the `viralpilot.userdata` table with the following structure:

```sql
CREATE TABLE viralpilot.userdata (
    cognito_user_id VARCHAR(255) PRIMARY KEY NOT NULL,
    username VARCHAR(255),
    email VARCHAR(255),
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
```

## Token Management

- **Admin tier**: Unlimited tokens (no consumption tracking)
- **Tester tier**: 1000 tokens per month, resets on the 1st of each month
- **Free tier**: 0 tokens (cannot make requests)
- **Other tiers**: To be defined

## Error Handling

The service includes comprehensive error handling for:
- Database connection issues
- Invalid subscription tiers
- Insufficient tokens
- User not found scenarios
- Configuration validation

## Development

### Adding New Features

1. Extend the `UserService` class in `user_service.py`
2. Add corresponding endpoints in `main.py`
3. Update schemas in `schemas.py` if needed
4. Add tests for new functionality

### Testing

```bash
# Test the service locally
python main.py

# Test with curl
curl http://localhost:8001/health
curl http://localhost:8001/tiers

# Test user creation
curl -X POST http://localhost:8001/user \
  -H "Content-Type: application/json" \
  -d '{"cognito_user_id": "test-user-123", "username": "testuser", "email": "test@example.com"}'
```

## Troubleshooting

### Common Issues

1. **Database Connection**: Ensure PostgreSQL is running and accessible
2. **Environment Variables**: Verify all required environment variables are set
3. **Port Conflicts**: Check if port 8001 is available
4. **Docker Issues**: Ensure Docker and Docker Compose are installed

### Logs

Check the application logs for detailed error information:
- Local: Console output
- Docker: `docker-compose logs user-management`

## License

This project is part of the Viral Pilot platform and follows the same licensing terms.