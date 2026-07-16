from fastapi import APIRouter, Depends, HTTPException, Cookie, Response, Request
from pydantic import BaseModel
import asyncpg
from typing import Optional

from app.services.oauth_provider import OAuthProvider
from app.services.google_oauth import GoogleOAuthProvider
from app.core.db import get_db_connection
from app.repositories.user_repository import UserRepository
from app.repositories.postgres_user_repository import PostgresUserRepository
from app.core.security import create_session_token, verify_session_token

router = APIRouter()

# Dependency function to inject the OAuth provider
def get_oauth_provider() -> OAuthProvider:
    return GoogleOAuthProvider()

# Dependency function to inject the User Repository
def get_user_repository(conn: asyncpg.Connection = Depends(get_db_connection)) -> UserRepository:
    return PostgresUserRepository(conn)

class CallbackRequest(BaseModel):
    code: str

@router.get("/login")
def get_login_url(provider: OAuthProvider = Depends(get_oauth_provider)):
    """
    Returns the URL to redirect the user to Google for OAuth authentication.
    """
    return {
        "url": provider.get_authorization_url()
    }

@router.post("/callback")
async def handle_callback(
    request_data: CallbackRequest,
    response: Response,
    request: Request,
    provider: OAuthProvider = Depends(get_oauth_provider),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Receives the OAuth code from the frontend, exchanges it for Google user info,
    sychronizes the user record in PostgreSQL, and generates an HttpOnly session cookie.
    """
    try:
        # 1. Fetch user profile from Google
        google_user = await provider.fetch_user_info(request_data.code)
        
        google_id = google_user.get("id") or google_user.get("sub")
        email = google_user.get("email")
        name = google_user.get("name")
        picture = google_user.get("picture")

        if not google_id or not email:
            raise HTTPException(
                status_code=400,
                detail="Incomplete user profile returned by Google."
            )

        # 2. Synchronize user record in database
        db_user = await user_repo.get_user_by_google_id(google_id)
        if db_user:
            synced_user = await user_repo.update_user(google_id, name, picture)
        else:
            synced_user = await user_repo.create_user(google_id, email, name, picture)

        # 3. Create secure session payload and encode in JWT
        user_payload = {
            "id": str(synced_user.get("id")),
            "email": synced_user.get("email"),
            "name": synced_user.get("name"),
            "picture": synced_user.get("picture")
        }
        session_token = create_session_token(user_payload)

        # 4. Determine secure cookie flag dynamically based on request protocol
        # (Allows HTTP on localhost for development, enforces Secure on HTTPS)
        is_secure = request.url.scheme == "https"

        response.set_cookie(
            key="mindguard_session",
            value=session_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=14 * 24 * 3600 # 14 days
        )

        return {
            "status": "success",
            "message": "User authenticated and session established."
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Authentication and session setup failed: {str(e)}"
        )

@router.get("/me")
async def get_me(
    mindguard_session: Optional[str] = Cookie(None)
):
    """
    Reads the HttpOnly mindguard_session cookie, validates the JWT signature,
    and returns the authenticated user's profile details.
    """
    if not mindguard_session:
        raise HTTPException(
            status_code=401,
            detail="Session cookie not found."
        )

    user_payload = verify_session_token(mindguard_session)
    if not user_payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session."
        )

    return {
        "status": "success",
        "user": user_payload
    }

@router.post("/logout")
def logout(response: Response, request: Request):
    """
    Deletes the HttpOnly session cookie, ending the user session.
    """
    is_secure = request.url.scheme == "https"
    
    response.delete_cookie(
        key="mindguard_session",
        httponly=True,
        secure=is_secure,
        samesite="lax"
    )
    return {
        "status": "success",
        "message": "Logged out successfully."
    }
