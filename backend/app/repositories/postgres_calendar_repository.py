import asyncpg
import uuid
from typing import Optional, Dict, Any, List
from app.repositories.calendar_repository import CalendarRepository

class PostgresCalendarRepository(CalendarRepository):
    def __init__(self, connection: asyncpg.Connection):
        self.conn = connection

    async def save_calendar_events(self, user_id: str, events_list: List[Dict[str, Any]]) -> int:
        if not events_list:
            return 0

        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        new_count = 0

        query = """
            INSERT INTO calendar_events (
                user_id, provider, external_id, title, description,
                organizer_name, organizer_email, start_time, end_time,
                timezone, location, attendees_count, status,
                created_at_google, updated_at_google
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            ON CONFLICT (external_id) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                start_time = EXCLUDED.start_time,
                end_time = EXCLUDED.end_time,
                location = EXCLUDED.location,
                attendees_count = EXCLUDED.attendees_count,
                status = EXCLUDED.status,
                updated_at_google = EXCLUDED.updated_at_google,
                synced_at = CURRENT_TIMESTAMP
            RETURNING (xmax = 0) AS is_new
        """

        for item in events_list:
            row = await self.conn.fetchrow(
                query,
                user_uuid,
                item.get("provider", "GOOGLE"),
                item.get("external_id"),
                item.get("title"),
                item.get("description"),
                item.get("organizer_name"),
                item.get("organizer_email"),
                item.get("start_time"),
                item.get("end_time"),
                item.get("timezone"),
                item.get("location"),
                item.get("attendees_count", 0),
                item.get("status"),
                item.get("created_at_google"),
                item.get("updated_at_google")
            )
            if row and row["is_new"]:
                new_count += 1

        return new_count
