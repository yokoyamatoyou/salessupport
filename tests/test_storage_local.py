import csv
import json
from pathlib import Path
from typing import Any, Dict

import pytest

from providers.storage_local import LocalStorageProvider


def test_save_and_load_session(tmp_path: Path):
    provider = LocalStorageProvider(data_dir=str(tmp_path))

    payload: Dict[str, Any] = {
        "type": "pre_advice",
        "input": {"industry": "IT"},
        "output": {"result": 1},
    }

    session_id = provider.save_session(payload, team_id="t0")
    assert isinstance(session_id, str) and len(session_id) > 0

    # ファイルが作成されている
    file_path = tmp_path / "sessions" / f"{session_id}.json"
    assert file_path.exists()

    # 読み出し
    data = provider.load_session(session_id)
    assert data["session_id"] == session_id
    assert data["data"] == payload
    assert data.get("pinned") is False
    assert data.get("tags") == []
    assert data.get("team_id") == "t0"


def test_set_pinned_and_list_order(tmp_path: Path):
    provider = LocalStorageProvider(data_dir=str(tmp_path))

    id_a = provider.save_session({"type": "pre_advice", "input": {}, "output": {}})
    id_b = provider.save_session({"type": "post_review", "input": {}, "output": {}})

    # ピン留め前は作成日時降順（id_bが先になる可能性が高い）
    sessions_before = provider.list_sessions()
    assert len(sessions_before) == 2

    # id_a をピン留め
    assert provider.set_pinned(id_a, True) is True

    # ピン留め後は id_a が先頭
    sessions_after = provider.list_sessions()
    assert sessions_after[0]["session_id"] == id_a
    assert sessions_after[0].get("pinned") is True


def test_update_tags_normalize(tmp_path: Path):
    provider = LocalStorageProvider(data_dir=str(tmp_path))
    session_id = provider.save_session({"type": "pre_advice", "input": {}, "output": {}})

    ok = provider.update_tags(session_id, [" 顧客A ", "優先", "優先", "", None])  # type: ignore[arg-type]
    assert ok is True

    loaded = provider.load_session(session_id)
    # 空白除去・空要素除外・重複排除
    assert loaded.get("tags") == ["顧客A", "優先"]


def test_delete_session(tmp_path: Path):
    provider = LocalStorageProvider(data_dir=str(tmp_path))
    session_id = provider.save_session({"type": "post_review", "input": {}, "output": {}})

    file_path = tmp_path / "sessions" / f"{session_id}.json"
    assert file_path.exists()

    assert provider.delete_session(session_id) is True
    assert not file_path.exists()

    with pytest.raises(FileNotFoundError):
        provider.load_session(session_id)


def test_export_sessions(tmp_path: Path):
    provider = LocalStorageProvider(data_dir=str(tmp_path))
    provider.save_session({"type": "pre_advice", "input": {}, "output": {}}, user_id="u1", team_id="t1", success=True)
    provider.save_session({"type": "post_review", "input": {}, "output": {}}, user_id="u2", team_id="t2", success=False)

    json_data = provider.export_sessions("json")
    parsed = json.loads(json_data)
    assert len(parsed) == 2
    assert {"session_id", "user_id", "team_id", "success"}.issubset(parsed[0].keys())

    csv_data = provider.export_sessions("csv")
    reader = csv.DictReader(csv_data.splitlines())
    rows = list(reader)
    assert len(rows) == 2
    assert {"session_id", "user_id", "team_id", "success"}.issubset(rows[0].keys())


def test_save_session_invalid_names(tmp_path: Path):
    provider = LocalStorageProvider(data_dir=str(tmp_path))
    with pytest.raises(ValueError):
        provider.save_session({}, session_id="../bad")
    with pytest.raises(ValueError):
        provider.save_session({}, session_id="bad/name")


def test_save_data_invalid_filename(tmp_path: Path):
    provider = LocalStorageProvider(data_dir=str(tmp_path))
    with pytest.raises(ValueError):
        provider.save_data("../bad.json", {})
    with pytest.raises(ValueError):
        provider.save_data("bad/name.json", {})


def test_tenant_creates_subdirectory(tmp_path: Path):
    provider = LocalStorageProvider(data_dir=str(tmp_path), tenant_id="tenant1")
    session_id = provider.save_session({"type": "pre_advice", "input": {}, "output": {}})
    expected_session = tmp_path / "tenant1" / "sessions" / f"{session_id}.json"
    assert expected_session.exists()

    provider.save_data("foo.json", {"a": 1})
    expected_data = tmp_path / "tenant1" / "foo.json"
    assert expected_data.exists()


