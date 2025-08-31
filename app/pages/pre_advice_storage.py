"""
Pre-advice storage functions - Extracted from main pre_advice.py for better maintainability
"""

from typing import Optional
import streamlit as st
from datetime import datetime

from core.models import SalesInput


def save_pre_advice(*, sales_input: SalesInput, advice: dict, selected_icebreaker: Optional[str] = None) -> str:
    """事前アドバイスの結果をセッション形式で保存し、Session IDを返す"""
    try:
        from services.storage_service import get_storage_provider

        provider = get_storage_provider()
        payload = {
            "type": "pre_advice",
            "input": sales_input.dict(),
            "output": {
                "advice": advice,
                "selected_icebreaker": selected_icebreaker,
            },
        }
        session_id = provider.save_session(payload)
        return session_id
    except Exception as e:
        st.error(f"保存に失敗しました: {str(e)}")
        raise
