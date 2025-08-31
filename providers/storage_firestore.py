import csv
import io
import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List

from google.cloud import firestore


class FirestoreStorageProvider:
    """Firestore based session storage provider."""

    def __init__(self, tenant_id: str, credentials_path: str | None = None) -> None:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        if credentials_path:
            if not os.path.exists(credentials_path):
                raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS file not found")
            self.client = firestore.Client.from_service_account_json(credentials_path)
        else:
            self.client = firestore.Client()
        self.tenant_id = tenant_id

    def _sessions_collection(self):
        return (
            self.client.collection("tenants")
            .document(self.tenant_id)
            .collection("sessions")
        )

    def _doc(self, session_id: str):
        return self._sessions_collection().document(session_id)

    def save_session(
        self,
        data: Dict[str, Any],
        session_id: str | None = None,
        user_id: str | None = None,
        team_id: str | None = None,
        success: bool | None = None,
    ) -> str:
        if session_id is None:
            session_id = str(uuid.uuid4())
        if user_id is None:
            user_id = os.getenv("USER_ID", "anonymous")
        if team_id is None:
            team_id = os.getenv("TEAM_ID", "unknown")
        if success is None:
            success = data.get("success", True)
        doc = self._doc(session_id)
        doc.set(
            {
                "session_id": session_id,
                "user_id": user_id,
                "team_id": team_id,
                "created_at": datetime.now().isoformat(),
                "success": bool(success),
                "pinned": False,
                "tags": [],
                "data": data,
            }
        )
        return session_id

    def load_session(self, session_id: str) -> Dict[str, Any]:
        doc = self._doc(session_id).get()
        if not doc.exists:
            raise FileNotFoundError(f"session {session_id} not found")
        return doc.to_dict()

    def list_sessions(self) -> List[Dict[str, Any]]:
        sessions: List[Dict[str, Any]] = []
        for doc in self._sessions_collection().stream():
            sessions.append(doc.to_dict())
        return sorted(
            sessions,
            key=lambda x: (x.get("pinned", False), x.get("created_at", "")),
            reverse=True,
        )

    def export_sessions(
        self,
        fmt: str = "json",
        sessions: List[Dict[str, Any]] | None = None,
    ) -> str:
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
        doc_ref = self._doc(session_id)
        doc = doc_ref.get()
        if not doc.exists:
            return False
        doc_ref.delete()
        return True

    def set_pinned(self, session_id: str, pinned: bool) -> bool:
        doc_ref = self._doc(session_id)
        doc = doc_ref.get()
        if not doc.exists:
            return False
        try:
            doc_ref.update({"pinned": bool(pinned)})
            return True
        except Exception:
            return False

    def update_tags(self, session_id: str, tags: List[str]) -> bool:
        doc_ref = self._doc(session_id)
        doc = doc_ref.get()
        if not doc.exists:
            return False
        try:
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
            doc_ref.update({"tags": normalized})
            return True
        except Exception:
            return False

    def save_data(self, filename: str, data: Dict[str, Any]) -> str:
        if "/" in filename:
            raise ValueError("Invalid filename")
        doc_ref = (
            self.client.collection("tenants")
            .document(self.tenant_id)
            .collection("data")
            .document(filename)
        )
        doc_ref.set(data)
        return filename
