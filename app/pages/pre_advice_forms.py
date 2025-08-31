"""
Pre-advice form components - Extracted from main pre_advice.py for better maintainability
"""

from typing import Dict, Any, Optional, Tuple
import streamlit as st
from translations import t

from components.copy_button import copy_button
from components.sales_type import get_sales_type_emoji
from app.components.sales_style_diagnosis import SalesStyleDiagnosis
from app.components.smart_defaults import SmartDefaultsManager
from core.models import SalesInput, SalesType, SalesStyle


def render_sales_style_selection() -> Optional[SalesStyle]:
    """営業スタイル選択UI（簡略化版）"""
    st.markdown("### 🎯 あなたの営業スタイル")

    diagnosis = SalesStyleDiagnosis()
    diagnosed_style = diagnosis.render_diagnosis_ui()

    if diagnosed_style:
        st.session_state.selected_sales_style = diagnosed_style
        st.session_state.sales_style_diagnosed = True
        st.success(f"✅ {diagnosis.get_style_info(diagnosed_style)['name']} を選択しました！")
        return diagnosed_style

    # 直接選択のフォールバック
    if st.checkbox("診断をスキップして直接選択する"):
        fallback_style = diagnosis.render_style_selector_fallback()
        if fallback_style:
            st.session_state.selected_sales_style = fallback_style
            st.session_state.sales_style_diagnosed = True
            return fallback_style

    return None


def render_simplified_form() -> Tuple[bool, Dict[str, Any]]:
    """簡略化された事前アドバイス入力フォーム（スマートデフォルト対応）"""
    if "pre_advice_form_data" not in st.session_state:
        st.session_state.pre_advice_form_data = {}

    # 営業スタイル選択
    selected_style = render_sales_style_selection()
    if not selected_style and not st.session_state.get("sales_style_diagnosed"):
        return False, {}

    # 基本情報入力
    st.markdown("---")
    st.markdown("### 📝 基本情報")

    smart_manager = SmartDefaultsManager()
    defaults = smart_manager.get_smart_defaults(selected_style, "")

    quickstart = st.session_state.get("quickstart_mode", False)

    with st.form("simplified_pre_advice"):
        # 業界入力
        industry = st.text_input(
            "業界 *",
            placeholder="例: IT、製造業、金融業",
            help="対象となる業界を入力してください",
            key="industry_input",
            value=st.session_state.pre_advice_form_data.get("industry", ""),
        )

        # 業界が変更されたらスマートデフォルトを更新
        if industry and industry != st.session_state.pre_advice_form_data.get("industry"):
            updated_defaults = smart_manager.get_smart_defaults(selected_style, industry)
            if updated_defaults != defaults:
                st.info("💡 業界に合わせてデフォルト値を更新しました")

        # 商品・サービス入力
        product = st.text_input(
            "商品・サービス" + (" *" if not quickstart else ""),
            placeholder="例: SaaS、コンサルティング",
            help="提供する商品・サービスを入力してください",
            key="product_input",
            value=st.session_state.pre_advice_form_data.get("product", ""),
        )

        # 目的入力（スマートデフォルト適用）
        purpose_help = "この商談の目的を入力してください"
        if defaults.get("purpose"):
            purpose_help += f"\n💡 例: {defaults['purpose']}"

        show_purpose = st.checkbox(
            "商談目的を指定する",
            value=bool(st.session_state.pre_advice_form_data.get("purpose")) or bool(defaults.get("purpose"))
        )

        purpose = ""
        if show_purpose:
            purpose = st.text_input(
                "商談目的",
                placeholder=defaults.get("purpose", "例: 新規顧客獲得、既存顧客拡大"),
                help=purpose_help,
                key="purpose_input",
                value=st.session_state.pre_advice_form_data.get("purpose", defaults.get("purpose", "")),
            )

        # 詳細設定（折りたたみ）
        with st.expander("詳細設定（オプション）", expanded=False):
            # 制約事項（スマートデフォルト適用）
            constraints_placeholder = "例: 予算制限、期間制限、技術制約"
            if defaults.get("constraints"):
                constraints_placeholder += f"\n💡 {defaults['constraints'][0]}"

            st.text_area(
                "制約事項",
                placeholder=constraints_placeholder,
                help="商談や提案における制約事項があれば入力してください",
                key="constraints_input",
                value=st.session_state.pre_advice_form_data.get("constraints", ""),
                height=100
            )

            # スタイル別Tips表示
            if selected_style:
                st.markdown("#### 💡 あなたの営業スタイルに適した設定")
                tips = smart_manager.get_communication_tips(selected_style)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**コミュニケーション:** {tips['tone']}")
                    st.markdown(f"**フォローアップ:** {tips['follow_up']}")
                with col2:
                    st.markdown(f"**KPI重視:** {defaults.get('kpi_focus', 'バランスよく')}")

                # 制約の提案
                suggested_constraints = smart_manager.suggest_constraints(selected_style, industry)
                if suggested_constraints:
                    st.markdown("**推奨される考慮事項:**")
                    for constraint in suggested_constraints[:3]:
                        st.markdown(f"• {constraint}")

        # ボタン配置
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            submitted = st.form_submit_button(
                "🚀 アドバイスを生成",
                type="primary",
                use_container_width=True
            )

    # フォームデータ更新
    if submitted:
        st.session_state.pre_advice_form_data.update({
            "industry": industry,
            "product": product,
            "purpose": purpose,
            "sales_style": selected_style,
        })

    return submitted, {
        "industry": industry,
        "product": product,
        "purpose": purpose,
        "sales_style": selected_style,
    }


def render_form() -> Tuple[bool, Dict[str, Any]]:
    """事前アドバイス入力フォーム（後方互換性維持）"""
    step_titles = ["基本情報", "詳細", "制約"]
    total_steps = len(step_titles)
    if "pre_form_step" not in st.session_state:
        st.session_state.pre_form_step = 1
    if "pre_advice_form_data" not in st.session_state:
        st.session_state.pre_advice_form_data = {}

    step = st.session_state.pre_form_step
    st.progress(step / total_steps)
    st.markdown(f"### {step_titles[step - 1]} ({step}/{total_steps})")

    quickstart = st.session_state.get("quickstart_mode", False)
    submitted = False
    skip_clicked = False

    if step == 1:
        with st.form("pre_advice_step1"):
            if quickstart:
                st.caption(t("later_help"))

            st.selectbox(
                "営業タイプ *",
                options=list(SalesType),
                format_func=lambda x: f"{x.value} ({get_sales_type_emoji(x)})",
                help="営業スタイルを選択してください",
                key="sales_type_select",
                on_change=update_form_data,
                args=("sales_type_select", "sales_type"),
            )

            industry = st.text_input(
                t("pre_advice_industry_label"),
                placeholder="例: IT、製造業、金融業",
                help="対象となる業界を入力してください（2文字以上）",
                key="industry_input",
                on_change=update_form_data,
                args=("industry_input", "industry"),
            )

            if industry:
                from core.validation import validate_industry
                industry_errors = validate_industry(industry)
                if industry_errors:
                    for error in industry_errors:
                        st.error(f"⚠️ {error}")
                else:
                    st.success("✅ 業界名が有効です")

            product_label_key = (
                "pre_advice_product_label"
                if not quickstart
                else "pre_advice_product_label_optional"
            )
            product = st.text_input(
                t(product_label_key),
                placeholder="例: SaaS、コンサルティング",
                help="提供する商品・サービスを入力してください（2文字以上）",
                key="product_input",
                on_change=update_form_data,
                args=("product_input", "product"),
            )

            if product:
                from core.validation import validate_product
                product_errors = validate_product(product)
                if product_errors:
                    for error in product_errors:
                        st.error(f"⚠️ {error}")
                else:
                    st.success("✅ 商品名が有効です")

            if quickstart:
                col1, col2 = st.columns(2)
                with col1:
                    skip_clicked = st.form_submit_button(
                        t("fill_later"), use_container_width=True
                    )
                with col2:
                    next_clicked = st.form_submit_button(
                        "次へ", type="primary", use_container_width=True
                    )
            else:
                next_clicked = st.form_submit_button(
                    "次へ", type="primary", use_container_width=True
                )

        if skip_clicked or next_clicked:
            st.session_state.pre_form_step = 2
            st.rerun()

    elif step == 2:
        with st.form("pre_advice_step2"):
            if quickstart:
                st.caption(t("later_help"))
            description_type = st.radio(
                "説明の入力方法",
                ["テキスト", "URL"],
                help="商品・サービスの説明をテキストで入力するか、URLで指定するかを選択してください",
                key="description_type",
                on_change=update_form_data,
                args=("description_type", "description_type"),
            )
            if description_type == "テキスト":
                st.session_state["description_url"] = None
                st.session_state.pre_advice_form_data["description_url"] = None
                st.text_area(
                    "説明",
                    placeholder="商品・サービスの詳細説明",
                    help="商品・サービスの特徴や価値を詳しく説明してください",
                    key="description_text",
                    on_change=update_form_data,
                    args=("description_text", "description"),
                )
            else:
                st.session_state["description_text"] = None
                st.session_state.pre_advice_form_data["description"] = None
                st.text_input(
                    "説明URL",
                    placeholder="https://example.com",
                    help="商品・サービスの説明が記載されているWebページのURLを入力してください",
                    key="description_url",
                    on_change=update_form_data,
                    args=("description_url", "description_url"),
                )

            competitor_type = st.radio(
                "競合の入力方法",
                ["テキスト", "URL"],
                help="競合情報をテキストで入力するか、URLで指定するかを選択してください",
                key="competitor_type",
                on_change=update_form_data,
                args=("competitor_type", "competitor_type"),
            )
            if competitor_type == "テキスト":
                st.session_state["competitor_url"] = None
                st.session_state.pre_advice_form_data["competitor_url"] = None
                st.text_input(
                    "競合",
                    placeholder="例: 競合A、競合B",
                    help="主要な競合企業やサービスを入力してください",
                    key="competitor_text",
                    on_change=update_form_data,
                    args=("competitor_text", "competitor"),
                )
            else:
                st.session_state["competitor_text"] = None
                st.session_state.pre_advice_form_data["competitor"] = None
                st.text_input(
                    "競合URL",
                    placeholder="https://competitor.com",
                    help="競合情報が記載されているWebページのURLを入力してください",
                    key="competitor_url",
                    on_change=update_form_data,
                    args=("competitor_url", "competitor_url"),
                )

            is_mobile = st.session_state.get("screen_width", 1000) < 600
            if is_mobile:
                if quickstart:
                    back_clicked = st.form_submit_button("戻る", use_container_width=True)
                    skip_clicked = st.form_submit_button(
                        t("fill_later"), use_container_width=True
                    )
                    next_clicked = st.form_submit_button(
                        "次へ", type="primary", use_container_width=True
                    )
                else:
                    back_clicked = st.form_submit_button(
                        "戻る", use_container_width=True
                    )
                    next_clicked = st.form_submit_button(
                        "次へ", type="primary", use_container_width=True
                    )
            else:
                if quickstart:
                    back_col, skip_col, next_col = st.columns(3)
                    with back_col:
                        back_clicked = st.form_submit_button(
                            "戻る", use_container_width=True
                        )
                    with skip_col:
                        skip_clicked = st.form_submit_button(
                            t("fill_later"), use_container_width=True
                        )
                    with next_col:
                        next_clicked = st.form_submit_button(
                            "次へ", type="primary", use_container_width=True
                        )
                else:
                    back_col, next_col = st.columns(2)
                    with back_col:
                        back_clicked = st.form_submit_button(
                            "戻る", use_container_width=True
                        )
                    with next_col:
                        next_clicked = st.form_submit_button(
                            "次へ", type="primary", use_container_width=True
                        )

        if back_clicked:
            st.session_state.pre_form_step = 1
            st.rerun()
        elif skip_clicked or next_clicked:
            st.session_state.pre_form_step = 3
            st.rerun()

    else:  # step == 3
        with st.form("pre_advice_step3"):
            if quickstart:
                st.caption(t("later_help"))
            stage_label = "商談ステージ *" if not quickstart else "商談ステージ"
            st.selectbox(
                stage_label,
                ["初期接触", "ニーズ発掘", "提案", "商談", "クロージング"],
                help="現在の商談の進行段階を選択してください",
                key="stage_select",
                on_change=update_form_data,
                args=("stage_select", "stage"),
            )

            purpose = st.text_input(
                "目的 *",
                placeholder="例: 新規顧客獲得、既存顧客拡大",
                help="この商談の目的を具体的に入力してください（5文字以上）",
                key="purpose_input",
                on_change=update_form_data,
                args=("purpose_input", "purpose"),
            )

            if purpose:
                from core.validation import validate_purpose
                purpose_errors = validate_purpose(purpose)
                if purpose_errors:
                    for error in purpose_errors:
                        st.error(f"⚠️ {error}")
                else:
                    st.success("✅ 目的が有効です")

            st.text_area(
                "制約",
                placeholder="例: 予算制限、期間制限、技術制約（改行で区切って入力）",
                help="商談や提案における制約事項があれば入力してください（各制約は3文字以上）",
                key="constraints_input",
                on_change=update_form_data,
                args=("constraints_input", "constraints_input"),
            )

            is_mobile = st.session_state.get("screen_width", 1000) < 600
            if is_mobile:
                if quickstart:
                    back_clicked = st.form_submit_button("戻る", use_container_width=True)
                    skip_clicked = st.form_submit_button(
                        t("fill_later"), use_container_width=True
                    )
                    submitted = st.form_submit_button(
                        "🚀 アドバイスを生成",
                        type="primary",
                        use_container_width=True,
                    )
                else:
                    back_clicked = st.form_submit_button(
                        "戻る", use_container_width=True
                    )
                    submitted = st.form_submit_button(
                        "🚀 アドバイスを生成",
                        type="primary",
                        use_container_width=True,
                    )
            else:
                if quickstart:
                    back_col, skip_col, submit_col = st.columns(3)
                    with back_col:
                        back_clicked = st.form_submit_button(
                            "戻る", use_container_width=True
                        )
                    with skip_col:
                        skip_clicked = st.form_submit_button(
                            t("fill_later"), use_container_width=True
                        )
                    with submit_col:
                        submitted = st.form_submit_button(
                            "🚀 アドバイスを生成",
                            type="primary",
                            use_container_width=True,
                        )
                else:
                    back_col, submit_col = st.columns(2)
                    with back_col:
                        back_clicked = st.form_submit_button(
                            "戻る", use_container_width=True
                        )
                    with submit_col:
                        submitted = st.form_submit_button(
                            "🚀 アドバイスを生成",
                            type="primary",
                            use_container_width=True,
                        )

        if back_clicked:
            st.session_state.pre_form_step = 2
            st.rerun()

    form_data = {
        "sales_type": st.session_state.pre_advice_form_data.get("sales_type")
        or st.session_state.get("sales_type_select"),
        "industry": st.session_state.pre_advice_form_data.get("industry")
        or st.session_state.get("industry_input"),
        "product": st.session_state.pre_advice_form_data.get("product")
        or st.session_state.get("product_input"),
        "description": st.session_state.pre_advice_form_data.get("description")
        or st.session_state.get("description_text"),
        "description_url": st.session_state.pre_advice_form_data.get("description_url")
        or st.session_state.get("description_url"),
        "competitor": st.session_state.pre_advice_form_data.get("competitor")
        or st.session_state.get("competitor_text"),
        "competitor_url": st.session_state.pre_advice_form_data.get("competitor_url")
        or st.session_state.get("competitor_url"),
        "stage": st.session_state.pre_advice_form_data.get("stage")
        or st.session_state.get("stage_select"),
        "purpose": st.session_state.pre_advice_form_data.get("purpose")
        or st.session_state.get("purpose_input"),
        "constraints_input": st.session_state.pre_advice_form_data.get(
            "constraints_input"
        )
        or st.session_state.get("constraints_input"),
    }
    return submitted or skip_clicked, form_data
