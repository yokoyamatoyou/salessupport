import os
from typing import Any, Dict

from providers.storage_local import LocalStorageProvider

try:
    from providers.storage_gcs import GCSStorageProvider  # type: ignore
except Exception:  # pragma: no cover
    GCSStorageProvider = None

try:
    from providers.storage_firestore import FirestoreStorageProvider  # type: ignore
except Exception:  # pragma: no cover
    FirestoreStorageProvider = None


def get_storage_provider():
    """Return storage provider based on environment"""
    app_env = os.getenv("APP_ENV", "local")
    provider_name = os.getenv("STORAGE_PROVIDER")
    if provider_name:
        provider = provider_name
    elif app_env == "gcp":
        provider = "firestore"
    elif app_env != "local":
        provider = "gcs"
    else:
        provider = "local"

    if provider == "gcs":
        if GCSStorageProvider is None:
            raise RuntimeError("GCSStorageProvider not available")
        bucket = os.getenv("GCS_BUCKET_NAME")
        if not bucket:
            raise RuntimeError("GCS_BUCKET_NAME environment variable is required for GCS storage")
        prefix = os.getenv("GCS_PREFIX", "sessions")
        if not prefix:
            raise RuntimeError("GCS_PREFIX environment variable is required for GCS storage")
        tenant_id = os.getenv("GCS_TENANT_ID")
        if not tenant_id:
            raise RuntimeError(
                "GCS_TENANT_ID environment variable is required for GCS storage"
            )
        return GCSStorageProvider(bucket_name=bucket, tenant_id=tenant_id, prefix=prefix)

    if provider == "firestore":
        if FirestoreStorageProvider is None:
            raise RuntimeError("FirestoreStorageProvider not available")
        credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or None
        tenant_id = os.getenv("FIRESTORE_TENANT_ID")
        if not tenant_id:
            raise RuntimeError(
                "FIRESTORE_TENANT_ID environment variable is required for Firestore storage",
            )
        return FirestoreStorageProvider(tenant_id=tenant_id, credentials_path=credentials)
    data_dir = os.getenv("DATA_DIR", "./data")
    tenant_id = os.getenv("LOCAL_TENANT_ID") or None
    return LocalStorageProvider(data_dir=data_dir, tenant_id=tenant_id)


def save_session(
    data: Dict[str, Any],
    session_id: str | None = None,
    user_id: str | None = None,
    team_id: str | None = None,
    success: bool | None = None,
) -> str:
    """Save session data with metadata using configured provider."""
    provider = get_storage_provider()
    return provider.save_session(
        data,
        session_id=session_id,
        user_id=user_id,
        team_id=team_id,
        success=success,
    )
