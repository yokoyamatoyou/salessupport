import csv
import io
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List
import os

from google.cloud import storage


class GCSStorageProvider:
    """Google Cloud Storage based session storage provider"""

    def __init__(
        self, bucket_name: str, tenant_id: str, prefix: str = "sessions"
    ) -> None:
        if not bucket_name:
            raise ValueError("bucket_name is required")
        if not tenant_id:
            raise ValueError("tenant_id is required")
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.prefix = f"{tenant_id}/{prefix.rstrip('/')}/"

    def _blob(self, session_id: str):
        return self.bucket.blob(f"{self.prefix}{session_id}.json")

    def save_session(
        self,
        data: Dict[str, Any],
        session_id: str | None = None,
        user_id: str | None = None,
        team_id: str | None = None,
        success: bool | None = None,
    ) -> str:
        """Save session data to GCS"""
        if session_id is None:
            session_id = str(uuid.uuid4())

        if user_id is None:
            user_id = os.getenv("USER_ID", "anonymous")
        if team_id is None:
            team_id = os.getenv("TEAM_ID", "unknown")
        if success is None:
            success = data.get("success", True)

        blob = self._blob(session_id)
        data_with_metadata = {
            "session_id": session_id,
            "user_id": user_id,
            "team_id": team_id,
            "created_at": datetime.now().isoformat(),
            "success": bool(success),
            "pinned": False,
            "tags": [],
            "data": data,
        }
        blob.upload_from_string(
            json.dumps(data_with_metadata, ensure_ascii=False, indent=2),
            content_type="application/json",
        )
        return session_id

    def load_session(self, session_id: str) -> Dict[str, Any]:
        """Load a session by id"""
        blob = self._blob(session_id)
        if not blob.exists():
            raise FileNotFoundError(f"session {session_id} not found")
        content = blob.download_as_text()
        return json.loads(content)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions"""
        sessions: List[Dict[str, Any]] = []
        for blob in self.client.list_blobs(self.bucket, prefix=self.prefix):
            if not blob.name.endswith(".json"):
                continue
            try:
                content = blob.download_as_text()
                sessions.append(json.loads(content))
            except Exception:
                continue
        return sorted(
            sessions,
            key=lambda x: (
                x.get("pinned", False),
                x.get("created_at", ""),
            ),
            reverse=True,
        )

    def export_sessions(
        self,
        fmt: str = "json",
        sessions: List[Dict[str, Any]] | None = None,
    ) -> str:
        """Export stored sessions in requested format"""
        if sessions is None:
            sessions = self.list_sessions()
        if fmt == "json":
            return json.dumps(sessions, ensure_ascii=False, indent=2)
        if fmt == "csv":
            output = io.StringIO()
            fieldnames = [
                "session_id",
                "user_id",
                "team_id",
                "created_at",
                "success",
                "pinned",
                "tags",
                "type",
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for s in sessions:
                writer.writerow(
                    {
                        "session_id": s.get("session_id"),
                        "user_id": s.get("user_id"),
                        "team_id": s.get("team_id"),
                        "created_at": s.get("created_at"),
                        "success": s.get("success"),
                        "pinned": s.get("pinned"),
                        "tags": ",".join(s.get("tags", [])),
                        "type": (s.get("data") or {}).get("type"),
                    }
                )
            return output.getvalue()
        raise ValueError("Unsupported format")

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        blob = self._blob(session_id)
        if not blob.exists():
            return False
        blob.delete()
        return True

    def set_pinned(self, session_id: str, pinned: bool) -> bool:
        """Update pinned state"""
        blob = self._blob(session_id)
        if not blob.exists():
            return False
        try:
            content = json.loads(blob.download_as_text())
            content["pinned"] = bool(pinned)
            blob.upload_from_string(
                json.dumps(content, ensure_ascii=False, indent=2),
                content_type="application/json",
            )
            return True
        except Exception:
            return False

    def update_tags(self, session_id: str, tags: List[str]) -> bool:
        """Overwrite tags"""
        blob = self._blob(session_id)
        if not blob.exists():
            return False
        try:
            content = json.loads(blob.download_as_text())
            normalized: List[str] = []
            seen = set()
            for t in tags:
                if not isinstance(t, str):
                    continue
                name = t.strip()
                if not name or name in seen:
                    continue
                seen.add(name)
                normalized.append(name)
            content["tags"] = normalized
            blob.upload_from_string(
                json.dumps(content, ensure_ascii=False, indent=2),
                content_type="application/json",
            )
            return True
        except Exception:
            return False

    def save_data(self, filename: str, data: Dict[str, Any]) -> str:
        """Save arbitrary data file"""
        blob = self.bucket.blob(f"{self.prefix}{filename}")
        blob.upload_from_string(
            json.dumps(data, ensure_ascii=False, indent=2),
            content_type="application/json",
        )
        return filename
