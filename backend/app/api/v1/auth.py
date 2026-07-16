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
    Receives the OAuth code from the frontend, exchanges it for Google user info,
    and synchronizes the user and integration records in PostgreSQL.
    Supports session-based authorization upgrades (e.g. connecting Gmail or Calendar).
    """
    try:
        # 1. Fetch user profile and scopes from Google
        google_user = await provider.fetch_user_info(request_data.code)
        
        google_id = google_user.get("id") or google_user.get("sub")
        email = google_user.get("email")
        name = google_user.get("name")
        picture = google_user.get("picture")
        granted_scopes = google_user.get("granted_scopes", "")

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
            # Flujo A: El usuario ya está logueado, estamos enlazando scopes adicionales (Gmail/Calendar)
            # Recuperamos los alcances existentes para fusionarlos (evitar sobrescrituras)
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
                scopes=unioned_scopes
            )
        else:
            # Flujo B: Primer ingreso / login estándar
            db_user = await user_repo.get_user_by_google_id(google_id)
            if db_user:
                synced_user = await user_repo.update_user(google_id, name, picture)
            else:
                synced_user = await user_repo.create_user(google_id, email, name, picture)
            
            user_id = str(synced_user.get("id"))

            # Registramos la integración por defecto, conservando/fusionando scopes antiguos si re-ingresa
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
                scopes=unioned_scopes
            )

            # Generamos token y cookie de sesión para el usuario
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
    Returns the real connection status of integrations by reading
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
        # Verificar si tiene autorización de lectura de Gmail
        if "https://www.googleapis.com/auth/gmail.readonly" in scopes:
            gmail_connected = True
        # Verificar si tiene autorización de lectura de Calendario
        if "https://www.googleapis.com/auth/calendar.readonly" in scopes:
            calendar_connected = True

    return {
        "google": google_connected,
        "gmail": gmail_connected,
        "calendar": calendar_connected
    }
