import csv
import io
import json
import os
from pathlib import Path
from typing import Dict, Any, List
import uuid
from datetime import datetime

class LocalStorageProvider:
    def __init__(self, data_dir: str = "./data", tenant_id: str | None = None):
        base_dir = Path(data_dir).resolve()
        if tenant_id:
            base_dir = base_dir / tenant_id
        self.data_dir = base_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir = self.data_dir / "sessions"
        self.sessions_dir.mkdir(exist_ok=True)
    
    def save_session(
        self,
        data: Dict[str, Any],
        session_id: str | None = None,
        user_id: str | None = None,
        team_id: str | None = None,
        success: bool | None = None,
    ) -> str:
        """セッションデータを保存"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        else:
            if ".." in session_id or "/" in session_id:
                raise ValueError("Invalid session_id")

        if user_id is None:
            user_id = os.getenv("USER_ID", "anonymous")
        if team_id is None:
            team_id = os.getenv("TEAM_ID", "unknown")
        if success is None:
            success = data.get("success", True)

        file_path = (self.sessions_dir / f"{session_id}.json").resolve()
        if not file_path.is_relative_to(self.data_dir):
            raise ValueError("Invalid session_id")
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

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_with_metadata, f, ensure_ascii=False, indent=2)

        return session_id
    
    def load_session(self, session_id: str) -> Dict[str, Any]:
        """セッションデータを読み込み"""
        file_path = self.sessions_dir / f"{session_id}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"セッション {session_id} が見つかりません")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """セッション一覧を取得"""
        sessions = []
        for file_path in self.sessions_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                    sessions.append(session_data)
            except Exception as e:
                print(f"セッションファイル {file_path} の読み込みに失敗: {e}")
        
        # ピン留めを上位、次に作成日時で降順
        # ピン留めを優先し、作成日時は降順（新しいものが上）
        return sorted(
            sessions,
            key=lambda x: (
                x.get("pinned", False),
                x.get("created_at", "")
            ),
            reverse=True,
        )

    def export_sessions(
        self,
        fmt: str = "json",
        sessions: List[Dict[str, Any]] | None = None,
    ) -> str:
        """保存済みセッションを指定フォーマットでエクスポート"""
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
        """セッションファイルを削除"""
        file_path = self.sessions_dir / f"{session_id}.json"
        if not file_path.exists():
            return False
        try:
            file_path.unlink()
            return True
        except Exception:
            return False

    def set_pinned(self, session_id: str, pinned: bool) -> bool:
        """ピン留め状態を更新"""
        file_path = self.sessions_dir / f"{session_id}.json"
        if not file_path.exists():
            return False
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            content["pinned"] = bool(pinned)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def update_tags(self, session_id: str, tags: List[str]) -> bool:
        """タグを上書き更新"""
        file_path = self.sessions_dir / f"{session_id}.json"
        if not file_path.exists():
            return False
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            # 正規化：空白除去、空要素除外、重複排除
            normalized = []
            seen = set()
            for t in tags:
                if not isinstance(t, str):
                    continue
                name = t.strip()
                if not name:
                    continue
                if name in seen:
                    continue
                seen.add(name)
                normalized.append(name)
            content["tags"] = normalized
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def save_data(self, filename: str, data: Dict[str, Any]) -> str:
        """任意データをファイルに保存"""
        if ".." in filename or "/" in filename:
            raise ValueError("Invalid filename")

        file_path = (self.data_dir / filename).resolve()
        if not file_path.is_relative_to(self.data_dir):
            raise ValueError("Invalid filename")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filename

