import csv
import importlib
import sys
import types

import pytest
from services import storage_service


class DummyProvider:
    def __init__(self, *args, **kwargs):
        pass


def test_gcs_requires_bucket(monkeypatch):
    monkeypatch.setenv("STORAGE_PROVIDER", "gcs")
    monkeypatch.delenv("GCS_BUCKET_NAME", raising=False)
    monkeypatch.delenv("GCS_PREFIX", raising=False)
    monkeypatch.setenv("GCS_TENANT_ID", "tenant")
    monkeypatch.setattr(storage_service, "GCSStorageProvider", DummyProvider)
    with pytest.raises(RuntimeError) as exc:
        storage_service.get_storage_provider()
    assert "GCS_BUCKET_NAME" in str(exc.value)


def test_gcs_requires_prefix(monkeypatch):
    monkeypatch.setenv("STORAGE_PROVIDER", "gcs")
    monkeypatch.setenv("GCS_BUCKET_NAME", "bucket")
    monkeypatch.setenv("GCS_PREFIX", "")
    monkeypatch.setenv("GCS_TENANT_ID", "tenant")
    monkeypatch.setattr(storage_service, "GCSStorageProvider", DummyProvider)
    with pytest.raises(RuntimeError) as exc:
        storage_service.get_storage_provider()
    assert "GCS_PREFIX" in str(exc.value)


def test_gcs_requires_tenant(monkeypatch):
    monkeypatch.setenv("STORAGE_PROVIDER", "gcs")
    monkeypatch.setenv("GCS_BUCKET_NAME", "bucket")
    monkeypatch.setenv("GCS_PREFIX", "sessions")
    monkeypatch.delenv("GCS_TENANT_ID", raising=False)
    monkeypatch.setattr(storage_service, "GCSStorageProvider", DummyProvider)
    with pytest.raises(RuntimeError) as exc:
        storage_service.get_storage_provider()
    assert "GCS_TENANT_ID" in str(exc.value)


def test_gcs_prefix_with_tenant(monkeypatch):
    monkeypatch.setenv("STORAGE_PROVIDER", "gcs")
    monkeypatch.setenv("GCS_BUCKET_NAME", "bucket")
    monkeypatch.setenv("GCS_PREFIX", "myprefix")
    monkeypatch.setenv("GCS_TENANT_ID", "tenant1")

    class DummyGCSProvider:
        def __init__(self, bucket_name, tenant_id, prefix):
            self.prefix = f"{tenant_id}/{prefix.rstrip('/')}/"
            self.saved = []
            self.list_prefix = None

        def list_sessions(self):
            self.list_prefix = self.prefix
            return []

        def save_data(self, filename, data):
            self.saved.append(f"{self.prefix}{filename}")
            return filename

    created = {}

    def provider_factory(bucket_name, tenant_id, prefix):
        dummy = DummyGCSProvider(bucket_name, tenant_id, prefix)
        created["instance"] = dummy
        return dummy

    monkeypatch.setattr(storage_service, "GCSStorageProvider", provider_factory)

    provider = storage_service.get_storage_provider()
    provider.save_data("foo.json", {"a": 1})
    provider.list_sessions()

    dummy = created["instance"]
    assert dummy.saved == ["tenant1/myprefix/foo.json"]
    assert dummy.list_prefix == "tenant1/myprefix/"


def test_local_storage_respects_tenant(monkeypatch, tmp_path):
    monkeypatch.delenv("STORAGE_PROVIDER", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("LOCAL_TENANT_ID", "tenantA")

    provider = storage_service.get_storage_provider()
    assert provider.data_dir == tmp_path / "tenantA"
    assert provider.sessions_dir == tmp_path / "tenantA" / "sessions"


def test_firestore_allows_default_credentials(monkeypatch):
    monkeypatch.setenv("STORAGE_PROVIDER", "firestore")
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.setenv("FIRESTORE_TENANT_ID", "tenant")

    captured = {}

    def provider_factory(*args, **kwargs):
        captured["credentials_path"] = kwargs.get("credentials_path")
        return DummyProvider()

    monkeypatch.setattr(storage_service, "FirestoreStorageProvider", provider_factory)

    storage_service.get_storage_provider()

    assert captured["credentials_path"] is None


def test_firestore_requires_tenant(monkeypatch):
    monkeypatch.setenv("STORAGE_PROVIDER", "firestore")
    monkeypatch.delenv("FIRESTORE_TENANT_ID", raising=False)
    monkeypatch.setattr(storage_service, "FirestoreStorageProvider", DummyProvider)
    with pytest.raises(RuntimeError) as exc:
        storage_service.get_storage_provider()
    assert "FIRESTORE_TENANT_ID" in str(exc.value)


def test_firestore_save_and_load(monkeypatch, tmp_path):
    class DummyFSProvider:
        def __init__(self, *args, **kwargs):
            self.sessions = {}

        def save_session(self, data, session_id=None, user_id=None, team_id=None, success=None):
            sid = session_id or "sid"
            self.sessions[sid] = {"session_id": sid, "data": data}
            return sid

        def load_session(self, session_id):
            return self.sessions[session_id]

    dummy_instance = DummyFSProvider()

    def provider_factory(*args, **kwargs):
        return dummy_instance

    credentials = tmp_path / "cred.json"
    credentials.write_text("{}")
    monkeypatch.delenv("STORAGE_PROVIDER", raising=False)
    monkeypatch.setenv("APP_ENV", "gcp")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(credentials))
    monkeypatch.setenv("FIRESTORE_TENANT_ID", "tenant")
    monkeypatch.setattr(storage_service, "FirestoreStorageProvider", provider_factory)

    payload = {"foo": "bar"}
    session_id = storage_service.save_session(payload)

    provider = storage_service.get_storage_provider()
    loaded = provider.load_session(session_id)
    assert loaded["data"] == payload


def test_firestore_export_sessions_csv(monkeypatch):
    dummy_firestore = types.SimpleNamespace()
    dummy_cloud = types.SimpleNamespace(firestore=dummy_firestore)
    monkeypatch.setitem(sys.modules, "google", types.SimpleNamespace(cloud=dummy_cloud))
    monkeypatch.setitem(sys.modules, "google.cloud", dummy_cloud)
    monkeypatch.setitem(sys.modules, "google.cloud.firestore", dummy_firestore)

    firestore_module = importlib.import_module("providers.storage_firestore")
    FirestoreStorageProvider = firestore_module.FirestoreStorageProvider

    provider = FirestoreStorageProvider.__new__(FirestoreStorageProvider)
    sessions = [
        {
            "session_id": "s1",
            "user_id": "u1",
            "team_id": "t1",
            "created_at": "2024-01-01T00:00:00",
            "success": True,
            "pinned": False,
            "tags": ["a", "b"],
            "data": {"type": "pre_advice"},
        },
        {
            "session_id": "s2",
            "user_id": "u2",
            "team_id": "t2",
            "created_at": "2024-01-02T00:00:00",
            "success": False,
            "pinned": True,
            "tags": ["x"],
            "data": {"type": "post_review"},
        },
    ]
    csv_output = provider.export_sessions("csv", sessions=sessions)
    reader = csv.DictReader(csv_output.splitlines())
    rows = list(reader)
    assert rows[0]["session_id"] == "s1"
    assert rows[0]["tags"] == "a,b"
    assert rows[1]["type"] == "post_review"
