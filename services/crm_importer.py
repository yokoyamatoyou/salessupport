import os
from typing import Any, Dict

import httpx


class CRMImporter:
    """Simple CRM API client"""

    def __init__(self, base_url: str | None = None) -> None:
        self.api_key = os.getenv("CRM_API_KEY")
        self.base_url = base_url or os.getenv("CRM_API_BASE", "https://example-crm.com/api")

    def fetch_customer(self, customer_id: str) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("CRM API key not set")
        url = f"{self.base_url}/customers/{customer_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = httpx.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
