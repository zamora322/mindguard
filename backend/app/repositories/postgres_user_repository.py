import asyncpg
import uuid
from typing import Optional, Dict, Any
from app.repositories.user_repository import UserRepository

class PostgresUserRepository(UserRepository):
    def __init__(self, connection: asyncpg.Connection):
        self.conn = connection

    async def get_user_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT id, google_id, email, name, picture, created_at, updated_at FROM users WHERE google_id = $1"
        row = await self.conn.fetchrow(query, google_id)
        return dict(row) if row else None

    async def create_user(
        self,
        google_id: str,
        email: str,
        name: str,
        picture: Optional[str]
    ) -> Dict[str, Any]:
        query = """
            INSERT INTO users (google_id, email, name, picture)
            VALUES ($1, $2, $3, $4)
            RETURNING id, google_id, email, name, picture, created_at, updated_at
        """
        row = await self.conn.fetchrow(query, google_id, email, name, picture)
        if not row:
            raise Exception("Failed to insert user record.")
        return dict(row)

    async def update_user(
        self,
        google_id: str,
        name: str,
        picture: Optional[str]
    ) -> Dict[str, Any]:
        query = """
            UPDATE users
            SET name = $1, picture = $2, updated_at = CURRENT_TIMESTAMP
            WHERE google_id = $3
            RETURNING id, google_id, email, name, picture, created_at, updated_at
        """
        row = await self.conn.fetchrow(query, name, picture, google_id)
        if not row:
            raise Exception(f"User with google_id {google_id} not found to update.")
        return dict(row)

    async def save_integration(
        self,
        user_id: str,
        provider: str,
        status: str,
        scopes: str,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None
    ) -> Dict[str, Any]:
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        
        query = """
            INSERT INTO user_integrations (user_id, provider, status, scopes, access_token, refresh_token)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id, provider)
            DO UPDATE SET
                status = EXCLUDED.status,
                scopes = EXCLUDED.scopes,
                access_token = COALESCE(EXCLUDED.access_token, user_integrations.access_token),
                refresh_token = COALESCE(EXCLUDED.refresh_token, user_integrations.refresh_token),
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, user_id, provider, status, scopes, access_token, refresh_token, connected_at, updated_at
        """
        row = await self.conn.fetchrow(query, user_uuid, provider, status, scopes, access_token, refresh_token)
        if not row:
            raise Exception("Failed to upsert integration record.")
        return dict(row)

    async def get_integrations(self, user_id: str) -> Optional[Dict[str, Any]]:
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        
        query = "SELECT id, user_id, provider, status, scopes, access_token, refresh_token, connected_at, updated_at FROM user_integrations WHERE user_id = $1 AND provider = $2"
        row = await self.conn.fetchrow(query, user_uuid, "google")
        return dict(row) if row else None
