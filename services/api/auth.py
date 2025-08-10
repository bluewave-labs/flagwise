import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from config import settings
from models import User, UserInDB, UserRole, Token, TokenData
from database import DatabaseService

# Password hashing - reduced rounds for development performance
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=4)

# JWT Security
security = HTTPBearer()

# Initialize database service
db_service = DatabaseService()

# Store the current admin password hash (will be updated when changed via UI)
# Generate with new bcrypt settings
_admin_password_hash = pwd_context.hash("admin123")

# Hardcoded admin user (keep separate from database users)
HARDCODED_ADMIN = UserInDB(
    username="admin",
    role=UserRole.ADMIN,
    hashed_password=_admin_password_hash
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user with username and password"""
    # Check hardcoded admin first
    if username == "admin":
        if verify_password(password, _admin_password_hash):
            # Update login timestamp for tracking
            return UserInDB(
                username="admin",
                role=UserRole.ADMIN,
                hashed_password=_admin_password_hash
            )
        return None
    
    # Check database users
    try:
        db_user = db_service.get_user_by_username(username)
        if db_user and db_user['is_active'] and verify_password(password, db_user['password_hash']):
            # Update login timestamp
            db_service.update_user_login(username)
            
            return UserInDB(
                username=db_user['username'],
                role=UserRole(db_user['role']),
                hashed_password=db_user['password_hash']
            )
    except Exception as e:
        print(f"Database error during authentication: {e}")
    
    return None

def update_admin_password(new_password: str):
    """Update the hardcoded admin password"""
    global _admin_password_hash
    _admin_password_hash = pwd_context.hash(new_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(username=username, role=UserRole(role))
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get the current authenticated user from JWT token"""
    token_data = verify_token(credentials.credentials)
    
    # Check database users (including admin)
    try:
        db_user = db_service.get_user_by_username(token_data.username)
        if db_user and db_user['is_active']:
            return User(
                username=db_user['username'], 
                role=UserRole(db_user['role']),
                first_name=db_user.get('first_name', ''),
                last_name=db_user.get('last_name', '')
            )
    except Exception as e:
        print(f"Database error during user lookup: {e}")
    
    # Fallback to hardcoded admin if database lookup fails
    if token_data.username == "admin":
        return User(username="admin", role=UserRole.ADMIN, first_name="", last_name="")
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not found or inactive",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that requires admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Alias for compatibility
require_admin = get_admin_user

def create_token_response(user: UserInDB) -> Token:
    """Create a token response for a user"""
    access_token_expires = timedelta(hours=settings.jwt_expiration_hours)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
        role=user.role
    )