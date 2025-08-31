import pytest
from unittest.mock import patch

from services.crm_importer import CRMImporter


def test_fetch_customer_success(monkeypatch):
    monkeypatch.setenv("CRM_API_KEY", "key")
    importer = CRMImporter(base_url="https://example.com")

    class DummyResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"industry": "IT"}

    def mock_get(url, headers=None, timeout=None):
        return DummyResponse()

    monkeypatch.setattr("services.crm_importer.httpx.get", mock_get)
    data = importer.fetch_customer("123")
    assert data["industry"] == "IT"


def test_fetch_customer_no_key(monkeypatch):
    monkeypatch.delenv("CRM_API_KEY", raising=False)
    importer = CRMImporter()
    with pytest.raises(ValueError):
        importer.fetch_customer("123")
