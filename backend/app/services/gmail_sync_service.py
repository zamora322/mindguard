import httpx
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.repositories.email_repository import EmailRepository
from app.core.config import settings

class GmailSyncService:
    def __init__(self, email_repo: EmailRepository):
        self.email_repo = email_repo
        self.profile_url = "https://gmail.googleapis.com/gmail/v1/users/me/profile"
        self.messages_list_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
        self.message_detail_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}"

    async def sync_user_emails(
        self,
        user_id: str,
        access_token: str,
        days: Optional[int] = None
    ) -> Dict[str, Any]:
        sync_days = days or settings.GMAIL_SYNC_DAYS

        # 1. Set state to syncing for provider 'gmail'
        await self.email_repo.upsert_sync_state(
            user_id=user_id,
            provider="gmail",
            status="syncing",
            synced_count=0
        )

        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            # Search query parameter for emails within the last X days
            query_str = f"newer_than:{sync_days}d"
            params = {"q": query_str, "maxResults": 500}

            async with httpx.AsyncClient(timeout=30.0) as client:
                # 2. Get current profile historyId from Gmail API
                account_history_id: Optional[str] = None
                profile_response = await client.get(self.profile_url, headers=headers)
                if profile_response.status_code == 200:
                    prof_data = profile_response.json()
                    if prof_data.get("historyId"):
                        account_history_id = str(prof_data.get("historyId"))

                # 3. Query Gmail API for message IDs within the specified day window
                list_response = await client.get(self.messages_list_url, headers=headers, params=params)
                if list_response.status_code != 200:
                    raise Exception(f"Failed to list Gmail messages: {list_response.text}")

                list_data = list_response.json()
                messages_summary = list_data.get("messages", [])

                if not messages_summary:
                    # No emails found
                    return await self.email_repo.upsert_sync_state(
                        user_id=user_id,
                        provider="gmail",
                        status="completed",
                        history_id=account_history_id,
                        synced_count=0
                    )

                # 4. Retrieve details for each email
                parsed_emails: List[Dict[str, Any]] = []

                for item in messages_summary:
                    msg_id = item.get("id")
                    detail_url = self.message_detail_url.format(id=msg_id)
                    detail_response = await client.get(detail_url, headers=headers, params={"format": "full"})

                    if detail_response.status_code == 200:
                        msg_data = detail_response.json()
                        parsed = self._parse_gmail_message(msg_data)
                        parsed_emails.append(parsed)

                # 5. Save parsed emails to database (counting only new insertions)
                inserted_count = await self.email_repo.save_emails(user_id, parsed_emails)

                # 6. Get the latest google_message_id and history_id
                latest_message_id = messages_summary[0].get("id") if messages_summary else None
                if not account_history_id and parsed_emails and parsed_emails[0].get("history_id"):
                    account_history_id = parsed_emails[0].get("history_id")

                # 7. Set state to completed with newly inserted count, last_message_id and history_id
                return await self.email_repo.upsert_sync_state(
                    user_id=user_id,
                    provider="gmail",
                    status="completed",
                    last_message_id=latest_message_id,
                    history_id=account_history_id,
                    synced_count=inserted_count
                )

        except Exception as e:
            print(f"Error during Gmail sync for user {user_id}: {e}")
            await self.email_repo.upsert_sync_state(
                user_id=user_id,
                provider="gmail",
                status="failed",
                synced_count=0
            )
            raise e

    def _parse_gmail_message(self, msg_data: dict) -> dict:
        google_message_id = msg_data.get("id")
        thread_id = msg_data.get("threadId")
        history_id = str(msg_data.get("historyId")) if msg_data.get("historyId") else None
        snippet = msg_data.get("snippet", "")
        label_ids = msg_data.get("labelIds", [])

        # Parse flags
        is_read = "UNREAD" not in label_ids
        is_starred = "STARRED" in label_ids

        # Parse date from internalDate (milliseconds)
        internal_date_ms = msg_data.get("internalDate")
        received_at = None
        if internal_date_ms:
            try:
                received_at = datetime.fromtimestamp(int(internal_date_ms) / 1000.0, tz=timezone.utc)
            except Exception:
                pass

        payload = msg_data.get("payload", {})
        headers = payload.get("headers", [])

        subject = ""
        sender_raw = ""

        for h in headers:
            name_lower = h.get("name", "").lower()
            if name_lower == "subject":
                subject = h.get("value", "")
            elif name_lower == "from":
                sender_raw = h.get("value", "")

        # Extract sender_name and sender_email
        sender_name = sender_raw
        sender_email = sender_raw
        if "<" in sender_raw and ">" in sender_raw:
            parts = sender_raw.split("<")
            sender_name = parts[0].strip(" \"'")
            sender_email = parts[1].replace(">", "").strip()

        # Attachments check
        has_attachments = False
        parts = payload.get("parts", [])
        for p in parts:
            if p.get("filename"):
                has_attachments = True
                break

        return {
            "google_message_id": google_message_id,
            "thread_id": thread_id,
            "history_id": history_id,
            "subject": subject,
            "sender_name": sender_name,
            "sender_email": sender_email,
            "snippet": snippet,
            "received_at": received_at,
            "is_read": is_read,
            "is_starred": is_starred,
            "has_attachments": has_attachments,
            "labels": label_ids
        }
