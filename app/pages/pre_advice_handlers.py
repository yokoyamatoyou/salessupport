"""
Pre-advice data handlers - Extracted from main pre_advice.py for better maintainability
"""

from typing import Dict, Any, Optional
import streamlit as st

from core.models import SalesInput, SalesType, SalesStyle


def update_form_data(src_key: str, dest_key: str) -> None:
    """セッションに入力値を保存"""
    st.session_state.pre_advice_form_data[dest_key] = st.session_state.get(src_key)


def apply_crm_data(data: dict) -> None:
    """CRMから取得したデータをフォームへ反映"""
    mapping = {
        "sales_type": "sales_type_select",
        "industry": "industry_input",
        "product": "product_input",
        "description": "description_text",
        "stage": "stage_select",
        "purpose": "purpose_input",
        "competitor": "competitor_text",
        "constraints": "constraints_input",
    }
    st.session_state.pre_advice_form_data.update(data)
    for key, widget_key in mapping.items():
        if key in data and data[key] is not None:
            value = data[key]
            if key == "sales_type" and not isinstance(value, SalesType):
                try:
                    value = SalesType(value)
                except Exception:
                    continue
            if key == "constraints" and isinstance(value, list):
                st.session_state[widget_key] = "\n".join(value)
            else:
                st.session_state[widget_key] = value


def process_form_data(form_data: dict) -> SalesInput:
    """フォームデータからSalesInputを生成（従来モード）"""
    constraints_input = form_data.get("constraints_input")
    constraints = (
        [c.strip() for c in constraints_input.split("\n") if c.strip()]
        if constraints_input
        else []
    )
    quickstart = st.session_state.get("quickstart_mode")
    return SalesInput(
        sales_type=form_data["sales_type"],
        industry=form_data["industry"],
        product=form_data["product"] or ("未入力" if quickstart else ""),
        description=form_data["description"],
        description_url=form_data["description_url"],
        competitor=form_data["competitor"],
        competitor_url=form_data["competitor_url"],
        stage=form_data["stage"] or ("初期接触" if quickstart else ""),
        purpose=form_data["purpose"],
        constraints=constraints,
    )


def process_simplified_form_data(form_data: dict) -> SalesInput:
    """簡略化フォームのデータをSalesInputに変換"""
    constraints_input = form_data.get("constraints", "")
    constraints = [c.strip() for c in constraints_input.split("\n") if c.strip()] if constraints_input else []

    # 営業スタイルを従来のSalesTypeにマッピング
    style_mapping = {
        SalesStyle.RELATIONSHIP_BUILDER: SalesType.RELATION,
        SalesStyle.PROBLEM_SOLVER: SalesType.PROBLEM_SOLVER,
        SalesStyle.VALUE_PROPOSER: SalesType.CHALLENGER,
        SalesStyle.SPECIALIST: SalesType.CONSULTANT,
        SalesStyle.DEAL_CLOSER: SalesType.CLOSER,
    }

    sales_type = style_mapping.get(form_data["sales_style"], SalesType.HUNTER)

    return SalesInput(
        sales_type=sales_type,
        industry=form_data["industry"],
        product=form_data["product"],
        description="",  # 簡略化モードでは使用しない
        description_url=None,
        competitor="",
        competitor_url=None,
        stage="初期接触",
        purpose=form_data.get("purpose", ""),
        constraints=constraints,
    )


def validate_input(sales_input: SalesInput) -> list:
    """SalesInputのバリデーション"""
    from core.validation import validate_sales_input
    return validate_sales_input(sales_input)
