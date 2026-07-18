import httpx
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from app.repositories.calendar_repository import CalendarRepository
from app.repositories.email_repository import EmailRepository
from app.core.config import settings

def parse_google_date(dt_obj: dict) -> Optional[datetime]:
    if not dt_obj:
        return None
    if dt_obj.get("dateTime"):
        try:
            return datetime.fromisoformat(dt_obj["dateTime"])
        except Exception:
            pass
    elif dt_obj.get("date"):
        try:
            return datetime.fromisoformat(dt_obj["date"]).replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return None

class GoogleCalendarSyncService:
    def __init__(self, calendar_repo: CalendarRepository, email_repo: EmailRepository):
        self.calendar_repo = calendar_repo
        self.email_repo = email_repo
        self.events_url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

    async def sync_user_calendar(
        self,
        user_id: str,
        access_token: str,
        days: Optional[int] = None
    ) -> Dict[str, Any]:
        sync_days = days or settings.CALENDAR_SYNC_DAYS

        # 1. Mark sync_state for provider 'calendar' as syncing
        await self.email_repo.upsert_sync_state(
            user_id=user_id,
            provider="calendar",
            status="syncing",
            synced_count=0
        )

        try:
            now = datetime.now(timezone.utc)
            time_min = now.isoformat()
            time_max = (now + timedelta(days=sync_days)).isoformat()

            headers = {"Authorization": f"Bearer {access_token}"}
            params = {
                "timeMin": time_min,
                "timeMax": time_max,
                "singleEvents": "true",
                "orderBy": "startTime"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.events_url, headers=headers, params=params)
                if response.status_code != 200:
                    raise Exception(f"Failed to list Google Calendar events: {response.text}")

                events_data = response.json()
                items = events_data.get("items", [])
                next_sync_token = events_data.get("nextSyncToken")

                if not items:
                    return await self.email_repo.upsert_sync_state(
                        user_id=user_id,
                        provider="calendar",
                        status="completed",
                        history_id=next_sync_token,
                        synced_count=0
                    )

                parsed_events: List[Dict[str, Any]] = []
                for item in items:
                    parsed = self._parse_calendar_event(item)
                    parsed_events.append(parsed)

                inserted_count = await self.calendar_repo.save_calendar_events(user_id, parsed_events)

                latest_event_id = items[0].get("id") if items else None

                return await self.email_repo.upsert_sync_state(
                    user_id=user_id,
                    provider="calendar",
                    status="completed",
                    last_message_id=latest_event_id,
                    history_id=next_sync_token,
                    synced_count=inserted_count
                )

        except Exception as e:
            print(f"Error during Google Calendar sync for user {user_id}: {e}")
            await self.email_repo.upsert_sync_state(
                user_id=user_id,
                provider="calendar",
                status="failed",
                synced_count=0
            )
            raise e

    def _parse_calendar_event(self, item: dict) -> dict:
        external_id = item.get("id")
        title = item.get("summary", "(Sin título)")
        description = item.get("description", "")
        location = item.get("location", "")
        status = item.get("status", "confirmed")

        organizer = item.get("organizer", {})
        organizer_name = organizer.get("displayName") or organizer.get("email", "")
        organizer_email = organizer.get("email", "")

        start_raw = item.get("start", {})
        end_raw = item.get("end", {})
        start_time = parse_google_date(start_raw)
        end_time = parse_google_date(end_raw)

        time_zone = start_raw.get("timeZone") or item.get("timeZone") or "UTC"
        attendees = item.get("attendees", [])

        created_raw = item.get("created")
        updated_raw = item.get("updated")
        created_at_google = datetime.fromisoformat(created_raw.replace("Z", "+00:00")) if created_raw else None
        updated_at_google = datetime.fromisoformat(updated_raw.replace("Z", "+00:00")) if updated_raw else None

        return {
            "provider": "GOOGLE",
            "external_id": external_id,
            "title": title,
            "description": description,
            "organizer_name": organizer_name,
            "organizer_email": organizer_email,
            "start_time": start_time,
            "end_time": end_time,
            "timezone": time_zone,
            "location": location,
            "attendees_count": len(attendees),
            "status": status,
            "created_at_google": created_at_google,
            "updated_at_google": updated_at_google
        }
