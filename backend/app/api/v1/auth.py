from fastapi import APIRouter, Depends, HTTPException, Cookie, Response, Request
from pydantic import BaseModel
import asyncpg
import asyncio
from typing import Optional

from app.services.oauth_provider import OAuthProvider
from app.services.google_oauth import GoogleOAuthProvider
from app.core.db import get_db_connection
from app.repositories.user_repository import UserRepository
from app.repositories.postgres_user_repository import PostgresUserRepository
from app.repositories.email_repository import EmailRepository
from app.repositories.postgres_email_repository import PostgresEmailRepository
from app.services.gmail_sync_service import GmailSyncService
from app.core.security import create_session_token, verify_session_token

router = APIRouter()

# Dependency injection functions
def get_oauth_provider() -> OAuthProvider:
    return GoogleOAuthProvider()

def get_user_repository(conn: asyncpg.Connection = Depends(get_db_connection)) -> UserRepository:
    return PostgresUserRepository(conn)

def get_email_repository(conn: asyncpg.Connection = Depends(get_db_connection)) -> EmailRepository:
    return PostgresEmailRepository(conn)

def get_gmail_sync_service(email_repo: EmailRepository = Depends(get_email_repository)) -> GmailSyncService:
    return GmailSyncService(email_repo)

async def run_gmail_sync_background(user_id: str, access_token: str):
    """
    Acquires its own database connection from the pool to run in background
    independently of the request context.
    """
    from app.core.db import db_pool
    if not db_pool:
        print("db_pool is not initialized, cannot run background sync")
        return

    try:
        async with db_pool.acquire() as conn:
            email_repo = PostgresEmailRepository(conn)
            service = GmailSyncService(email_repo)
            await service.sync_user_emails(user_id=user_id, access_token=access_token)
    except Exception as e:
        print(f"Background Gmail sync error for user {user_id}: {e}")

class CallbackRequest(BaseModel):
    code: str

@router.get("/login")
def get_login_url(
    scope_type: Optional[str] = None,
    provider: OAuthProvider = Depends(get_oauth_provider)
):
    """
    Returns the URL to redirect the user to Google for OAuth authentication.
    Appends extra scopes (like Gmail or Calendar) depending on the scope_type requested.
    """
    scopes = "openid email profile"
    if scope_type == "gmail":
        scopes += " https://www.googleapis.com/auth/gmail.readonly"
    elif scope_type == "calendar":
        scopes += " https://www.googleapis.com/auth/calendar.readonly"
    
    return {
        "url": provider.get_authorization_url(scopes=scopes)
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
    Receives the OAuth code from the frontend, exchanges it for Google user info and tokens,
    synchronizes user/integration records in PostgreSQL, and triggers email sync if Gmail scope is granted.
    """
    try:
        # 1. Fetch user profile, tokens and granted scopes from Google
        google_user = await provider.fetch_user_info(request_data.code)
        
        google_id = google_user.get("id") or google_user.get("sub")
        email = google_user.get("email")
        name = google_user.get("name")
        picture = google_user.get("picture")
        granted_scopes = google_user.get("granted_scopes", "")
        access_token = google_user.get("access_token")
        refresh_token = google_user.get("refresh_token")

        if not google_id or not email:
            raise HTTPException(
                status_code=400,
                detail="Incomplete user profile returned by Google."
            )

        # 2. Check if a session already exists (adding an integration to a logged-in user)
        mindguard_session = request.cookies.get("mindguard_session")
        user_id = None
        
        if mindguard_session:
            session_payload = verify_session_token(mindguard_session)
            if session_payload:
                user_id = session_payload.get("id")

        if user_id:
            # Flujo A: Usuario ya logueado, enlazando integración adicional
            existing = await user_repo.get_integrations(user_id)
            existing_scopes = set()
            if existing:
                existing_scopes = set(existing.get("scopes", "").split())
            
            new_scopes = set(granted_scopes.split())
            unioned_scopes = " ".join(existing_scopes.union(new_scopes))

            await user_repo.save_integration(
                user_id=user_id,
                provider="google",
                status="connected",
                scopes=unioned_scopes,
                access_token=access_token,
                refresh_token=refresh_token
            )
        else:
            # Flujo B: Primer ingreso / login estándar
            db_user = await user_repo.get_user_by_google_id(google_id)
            if db_user:
                synced_user = await user_repo.update_user(google_id, name, picture)
            else:
                synced_user = await user_repo.create_user(google_id, email, name, picture)
            
            user_id = str(synced_user.get("id"))

            existing = await user_repo.get_integrations(user_id)
            existing_scopes = set()
            if existing:
                existing_scopes = set(existing.get("scopes", "").split())
            
            new_scopes = set(granted_scopes.split())
            unioned_scopes = " ".join(existing_scopes.union(new_scopes))

            await user_repo.save_integration(
                user_id=user_id,
                provider="google",
                status="connected",
                scopes=unioned_scopes,
                access_token=access_token,
                refresh_token=refresh_token
            )

            user_payload = {
                "id": user_id,
                "email": synced_user.get("email"),
                "name": synced_user.get("name"),
                "picture": synced_user.get("picture")
            }
            session_token = create_session_token(user_payload)

            is_secure = request.url.scheme == "https"
            response.set_cookie(
                key="mindguard_session",
                value=session_token,
                httponly=True,
                secure=is_secure,
                samesite="lax",
                max_age=14 * 24 * 3600 # 14 days
            )

        # 3. Trigger initial email sync in background if Gmail scope is granted
        if "https://www.googleapis.com/auth/gmail.readonly" in unioned_scopes and access_token:
            asyncio.create_task(
                run_gmail_sync_background(user_id=user_id, access_token=access_token)
            )

        return {
            "status": "success",
            "message": "Authentication and integration synchronization completed."
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Authentication and scope sync failed: {str(e)}"
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

@router.get("/integrations")
async def get_integrations(
    mindguard_session: Optional[str] = Cookie(None),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Returns the connection status of integrations by reading
    scopes from the user_integrations table for the current user.
    """
    if not mindguard_session:
        raise HTTPException(
            status_code=401,
            detail="Active session cookie not found."
        )

    user_payload = verify_session_token(mindguard_session)
    if not user_payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session."
        )

    user_id = user_payload.get("id")
    integration = await user_repo.get_integrations(user_id)

    google_connected = False
    gmail_connected = False
    calendar_connected = False

    if integration and integration.get("status") == "connected":
        google_connected = True
        scopes = integration.get("scopes", "")
        if "https://www.googleapis.com/auth/gmail.readonly" in scopes:
            gmail_connected = True
        if "https://www.googleapis.com/auth/calendar.readonly" in scopes:
            calendar_connected = True

    return {
        "google": google_connected,
        "gmail": gmail_connected,
        "calendar": calendar_connected
    }

@router.get("/sync-status")
async def get_sync_status(
    mindguard_session: Optional[str] = Cookie(None),
    email_repo: EmailRepository = Depends(get_email_repository),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Returns the current email synchronization progress and state for the logged-in user.
    Auto-triggers background sync if Gmail is connected but sync hasn't run yet.
    """
    if not mindguard_session:
        raise HTTPException(
            status_code=401,
            detail="Active session cookie not found."
        )

    user_payload = verify_session_token(mindguard_session)
    if not user_payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session."
        )

    user_id = user_payload.get("id")
    state = await email_repo.get_sync_state(user_id, provider="google")

    if not state or state.get("status") == "idle":
        # Check if user has access_token in user_integrations to trigger sync
        integration = await user_repo.get_integrations(user_id)
        if (
            integration 
            and integration.get("access_token") 
            and "https://www.googleapis.com/auth/gmail.readonly" in integration.get("scopes", "")
        ):
            access_token = integration.get("access_token")
            # Set state immediately to syncing
            await email_repo.upsert_sync_state(user_id=user_id, provider="google", status="syncing", synced_count=0)
            asyncio.create_task(run_gmail_sync_background(user_id=user_id, access_token=access_token))
            return {
                "status": "syncing",
                "synced_count": 0,
                "last_message_id": None,
                "history_id": None
            }

        return {
            "status": "idle",
            "synced_count": 0,
            "last_message_id": None,
            "history_id": None
        }

    return {
        "status": state.get("status", "completed"),
        "synced_count": state.get("synced_count", 0),
        "last_message_id": state.get("last_message_id"),
        "history_id": state.get("history_id"),
        "last_sync": state.get("last_sync").isoformat() if state.get("last_sync") else None
    }
