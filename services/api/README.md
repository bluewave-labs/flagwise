# Shadow AI Detection API

FastAPI REST service providing secure access to LLM traffic monitoring data with JWT authentication and role-based access control.

## Features

### Authentication & Authorization
- **JWT Token Authentication** with role-based access
- **Two User Roles:**
  - `admin`: Full access including rule management
  - `read_only`: View data only, no modifications
- **Default Users:**
  - Username: `admin`, Password: `admin123`
  - Username: `viewer`, Password: `viewer123`

### Security
- **Data Truncation**: Prompts truncated to 200 chars for read-only users
- **Admin-only endpoints**: Rule CRUD operations protected
- **CORS enabled** for web dashboard integration
- **Input validation** with Pydantic models

## API Endpoints

### Authentication
- `POST /auth/login` - User login, returns JWT token
- `GET /auth/me` - Get current user info

### Health & Monitoring
- `GET /health` - System health check
- `GET /stats/totals?days=30` - System statistics

### LLM Requests
- `GET /requests` - Paginated list with filters
  - Filters: `flagged`, `provider`, `model`, `src_ip`, `min_risk_score`, `max_risk_score`, `start_date`, `end_date`, `search`
  - Pagination: `page`, `page_size` (max 1000)
- `GET /requests/{id}` - Single request details

### Detection Rules (Admin Only)
- `GET /rules` - List all detection rules
- `POST /rules` - Create new rule
- `PUT /rules/{id}` - Update existing rule
- `DELETE /rules/{id}` - Delete rule

## Data Models

### Request Response (Read-only users)
```json
{
  "id": "uuid",
  "timestamp": "2025-08-07T10:30:00Z",
  "src_ip": "192.168.1.100",
  "provider": "openai",
  "model": "gpt-4",
  "prompt_preview": "First 200 characters...",
  "risk_score": 75,
  "is_flagged": true,
  "flag_reason": "Critical Keywords, Email Pattern"
}
```

### Request Detail (Admin users)
Same as above plus:
```json
{
  "prompt": "Full prompt text",
  "response": "Full response text",
  "headers": {"Authorization": "Bearer sk-***"}
}
```

### Detection Rule
```json
{
  "id": "uuid",
  "name": "Critical Keywords",
  "rule_type": "keyword",
  "pattern": "password,secret,api_key",
  "severity": "critical",
  "points": 50,
  "is_active": true
}
```

## Configuration

Environment variables:
```bash
# Database
POSTGRES_HOST=postgres
POSTGRES_DB=shadow_ai
POSTGRES_USER=shadow_user
POSTGRES_PASSWORD=shadow_pass

# JWT Security
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
PROMPT_TRUNCATE_LENGTH=200
```

## Usage

### Running the API
```bash
# Via Docker Compose
docker-compose up api

# Development mode
cd services/api
python -m uvicorn main:app --reload --port 8000
```

### Testing
```bash
# Test all endpoints
python test_api.py

# Manual testing via curl
curl -X POST "http://localhost:8000/auth/login?username=admin&password=admin123"
curl -H "Authorization: Bearer <token>" "http://localhost:8000/requests?page=1&page_size=10"
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Performance
- **Pagination**: Efficient offset-based pagination
- **Database indexes**: Optimized queries for filtering
- **Connection pooling**: PostgreSQL connection management
- **Response truncation**: Reduced payload size for security

## Security Considerations
- Change default passwords in production
- Use strong JWT secret key
- Enable HTTPS in production
- Regular token rotation recommended
- Audit logs for admin operations