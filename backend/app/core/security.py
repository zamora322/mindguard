import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.core.config import settings

ALGORITHM = "HS256"
SESSION_LIFETIME_DAYS = 14

def create_session_token(data: dict) -> str:
    """
    Creates a signed JWT access token containing user profile information.
    """
    to_encode = data.copy()
    # Expire the token in 14 days
    expire = datetime.now(timezone.utc) + timedelta(days=SESSION_LIFETIME_DAYS)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_session_token(token: str) -> Optional[dict]:
    """
    Verifies the signature and expiration of a user session JWT.
    Returns the decoded payload if valid, otherwise None.
    """
    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return decoded
    except jwt.PyJWTError:
        return None
