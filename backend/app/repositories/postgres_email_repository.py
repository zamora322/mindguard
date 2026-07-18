import asyncpg
import uuid
import json
from typing import Optional, Dict, Any, List
from app.repositories.email_repository import EmailRepository

class PostgresEmailRepository(EmailRepository):
    def __init__(self, connection: asyncpg.Connection):
        self.conn = connection

    async def save_emails(self, user_id: str, email_list: List[Dict[str, Any]]) -> int:
        if not email_list:
            return 0

        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        count = 0

        query = """
            INSERT INTO emails (
                user_id, google_message_id, thread_id, subject, sender_name, sender_email,
                snippet, received_at, is_read, is_starred, has_attachments, labels
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb)
            ON CONFLICT (google_message_id) DO UPDATE SET
                subject = EXCLUDED.subject,
                snippet = EXCLUDED.snippet,
                is_read = EXCLUDED.is_read,
                is_starred = EXCLUDED.is_starred,
                labels = EXCLUDED.labels,
                synced_at = CURRENT_TIMESTAMP
        """

        for item in email_list:
            labels_json = json.dumps(item.get("labels", []))
            await self.conn.execute(
                query,
                user_uuid,
                item.get("google_message_id"),
                item.get("thread_id"),
                item.get("subject"),
                item.get("sender_name"),
                item.get("sender_email"),
                item.get("snippet"),
                item.get("received_at"),
                item.get("is_read", False),
                item.get("is_starred", False),
                item.get("has_attachments", False),
                labels_json
            )
            count += 1

        return count

    async def upsert_sync_state(
        self,
        user_id: str,
        provider: str,
        status: str,
        last_message_id: Optional[str] = None,
        history_id: Optional[str] = None,
        synced_count: int = 0
    ) -> Dict[str, Any]:
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

        query = """
            INSERT INTO sync_state (user_id, provider, status, last_message_id, history_id, synced_count, last_sync)
            VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id, provider) DO UPDATE SET
                status = EXCLUDED.status,
                last_message_id = COALESCE(EXCLUDED.last_message_id, sync_state.last_message_id),
                history_id = COALESCE(EXCLUDED.history_id, sync_state.history_id),
                synced_count = EXCLUDED.synced_count,
                last_sync = CURRENT_TIMESTAMP
            RETURNING id, user_id, provider, status, last_message_id, history_id, synced_count, last_sync, created_at
        """
        row = await self.conn.fetchrow(query, user_uuid, provider, status, last_message_id, history_id, synced_count)
        if not row:
            raise Exception("Failed to upsert sync_state record.")
        return dict(row)

    async def get_sync_state(self, user_id: str, provider: str = "google") -> Optional[Dict[str, Any]]:
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

        query = "SELECT id, user_id, provider, status, last_message_id, history_id, synced_count, last_sync, created_at FROM sync_state WHERE user_id = $1 AND provider = $2"
        row = await self.conn.fetchrow(query, user_uuid, provider)
        return dict(row) if row else None
