import streamlit as st
from core.models import SalesType

# Streamlit UI component helpers

def get_sales_type_emoji(sales_type: SalesType) -> str:
    """営業タイプに対応する絵文字を返す"""
    emoji_map = {
        SalesType.HUNTER: "🏹",
        SalesType.CLOSER: "🔒",
        SalesType.RELATION: "🤝",
        SalesType.CONSULTANT: "🧭",
        SalesType.CHALLENGER: "⚡",
        SalesType.STORYTELLER: "📖",
        SalesType.ANALYST: "📊",
        SalesType.PROBLEM_SOLVER: "🧩",
        SalesType.FARMER: "🌾",
    }
    return emoji_map.get(sales_type, "💼")


def sales_type_selectbox(*, key: str) -> SalesType:
    """営業タイプを選択するセレクトボックスを表示"""
    return st.selectbox(
        "営業タイプ *",
        options=list(SalesType),
        format_func=lambda x: f"{x.value} ({get_sales_type_emoji(x)})",
        help="営業スタイルを選択してください",
        key=key,
    )
