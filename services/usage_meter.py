import os
from typing import Dict

class UsageMeter:
    """Simple in-memory usage meter for tracking token usage per user or tenant."""

    _usage: Dict[str, int] = {}

    @classmethod
    def get_limit(cls, user_id: str | None = None) -> int:
        """Retrieve token limit for a user from env var TOKEN_USAGE_LIMIT."""
        return int(os.getenv("TOKEN_USAGE_LIMIT", "1000000"))

    @classmethod
    def add_tokens(cls, user_id: str, tokens: int) -> int:
        total = cls._usage.get(user_id, 0) + tokens
        cls._usage[user_id] = total
        return total

    @classmethod
    def get_tokens(cls, user_id: str) -> int:
        return cls._usage.get(user_id, 0)

    @classmethod
    def reset(cls):
        cls._usage.clear()
