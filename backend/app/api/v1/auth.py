from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import asyncpg
from typing import Optional

from app.services.oauth_provider import OAuthProvider
from app.services.google_oauth import GoogleOAuthProvider
from app.core.db import get_db_connection
from app.repositories.user_repository import UserRepository
from app.repositories.postgres_user_repository import PostgresUserRepository

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
    provider: OAuthProvider = Depends(get_oauth_provider),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Receives the OAuth code from the frontend, exchanges it for Google user info,
    then synchronizes (INSERT / UPDATE) the user record in the PostgreSQL database.
    """
    try:
        # 1. Fetch user profile from Google
        google_user = await provider.fetch_user_info(request_data.code)
        
        # Google user info key mappings (can return 'id' or OIDC 'sub')
        google_id = google_user.get("id") or google_user.get("sub")
        email = google_user.get("email")
        name = google_user.get("name")
        picture = google_user.get("picture")

        if not google_id or not email:
            raise HTTPException(
                status_code=400,
                detail="Incomplete user profile returned by Google."
            )

        # 2. Check if the google_id already exists in the database
        db_user = await user_repo.get_user_by_google_id(google_id)
        
        if db_user:
            # 3. YES: Update their name and avatar picture
            synced_user = await user_repo.update_user(google_id, name, picture)
        else:
            # 4. NO: Insert a new user record
            synced_user = await user_repo.create_user(google_id, email, name, picture)

        # 5. Return the synchronized database record
        return {
            "status": "success",
            "user": {
                "id": str(synced_user.get("id")),
                "google_id": synced_user.get("google_id"),
                "email": synced_user.get("email"),
                "name": synced_user.get("name"),
                "picture": synced_user.get("picture"),
                "created_at": synced_user.get("created_at").isoformat() if synced_user.get("created_at") else None,
                "updated_at": synced_user.get("updated_at").isoformat() if synced_user.get("updated_at") else None,
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Authentication and sync failed: {str(e)}"
        )
