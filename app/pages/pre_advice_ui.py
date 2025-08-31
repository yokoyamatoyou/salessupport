"""
Pre-advice UI rendering functions - Extracted from main pre_advice.py for better maintainability
"""

import json
from typing import Dict, Any
import streamlit as st
from datetime import datetime

from core.models import SalesInput
from components.copy_button import copy_button


def display_result(advice: dict, sales_input: SalesInput) -> None:
    """生成結果の表示"""
    if st.session_state.get("selected_icebreaker"):
        st.markdown("### ❄️ アイスブレイク（選択中）")
        st.markdown(f"> {st.session_state.selected_icebreaker}")

    display_advice(advice)
    render_save_section(sales_input, advice)


def display_advice(advice: dict) -> None:
    """アドバイスの表示（大幅に簡略化）"""
    st.markdown("---")
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        text-align: center;
        color: white;
    ">
        <h2 style="margin: 0; color: white;">🎯 生成されたアドバイス</h2>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">営業戦略とアクションプランをご確認ください</p>
    </div>
    """, unsafe_allow_html=True)

    # 短期戦略
    if "short_term" in advice:
        st.markdown("### 📅 短期戦略（1-2週間）")
        short_term = advice["short_term"]

        if "openers" in short_term:
            st.markdown("#### 🎭 開幕スクリプト")
            openers = short_term["openers"]

            tab1, tab2, tab3 = st.tabs(["📞 電話", "🚪 訪問", "📧 メール"])

            with tab1:
                if "call" in openers and openers["call"]:
                    st.markdown("**電話での開幕スクリプト：**")
                    st.markdown(f"```\n{openers['call']}\n```")
                    copy_button(openers["call"], key="copy_call")

            with tab2:
                if "visit" in openers and openers["visit"]:
                    st.markdown("**訪問時の開幕スクリプト：**")
                    st.markdown(f"```\n{openers['visit']}\n```")
                    copy_button(openers["visit"], key="copy_visit")

            with tab3:
                if "email" in openers and openers["email"]:
                    st.markdown("**メールでの開幕スクリプト：**")
                    st.markdown(f"```\n{openers['email']}\n```")
                    copy_button(openers["email"], key="copy_email")

        # 探索質問と差別化ポイントを簡略化して表示
        if "discovery" in short_term and short_term["discovery"]:
            st.markdown("#### 🔍 探索質問")
            for i, question in enumerate(short_term["discovery"][:3], 1):  # 最初の3つだけ表示
                st.markdown(f"{i}. {question}")
                copy_button(question, key=f"copy_discovery_{i}")

        if "differentiation" in short_term and short_term["differentiation"]:
            st.markdown("#### 🎯 競合との差別化ポイント")
            for i, diff in enumerate(short_term["differentiation"][:2], 1):  # 最初の2つだけ表示
                if isinstance(diff, dict) and "talk" in diff:
                    st.markdown(f"**vs {diff.get('vs', '競合')}：** {diff['talk']}")
                    copy_button(diff["talk"], key=f"copy_diff_{i}")
                else:
                    st.markdown(f"{i}. {diff}")
                    copy_button(diff, key=f"copy_diff_{i}")

    # 全体的なアドバイス（フォールバック用）
    if "overall_advice" in advice:
        st.markdown("### 💡 全体的なアドバイス")
        st.info(advice["overall_advice"])


def render_save_section(sales_input: SalesInput, advice: dict) -> None:
    """結果保存ボタンと処理"""
    if st.button("💾 生成結果を保存", use_container_width=False):
        try:
            from .pre_advice_storage import save_pre_advice

            session_id = save_pre_advice(
                sales_input=sales_input,
                advice=advice,
                selected_icebreaker=st.session_state.get("selected_icebreaker"),
            )
            st.session_state.pre_advice_session_id = session_id

            st.success("✅ 結果を保存しました！")

            st.markdown("---")
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    padding: 25px;
                    border-radius: 15px;
                    margin: 20px 0;
                    text-align: center;
                    color: white;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                ">
                    <h3 style="margin: 0; color: white; font-size: 1.5em;">💾 保存完了</h3>
                    <p style="margin: 15px 0; opacity: 0.9; font-size: 1.1em;">セッションが正常に保存されました</p>
                    <div style="
                        background: rgba(255, 255, 255, 0.2);
                        padding: 15px;
                        border-radius: 10px;
                        margin: 15px 0;
                        font-family: monospace;
                        font-size: 1.2em;
                        letter-spacing: 1px;
                    ">
                        <strong>セッションID:</strong> {session_id}
                    </div>
                    <p style="margin: 10px 0 0 0; opacity: 0.8; font-size: 0.9em;">
                        📁 保存場所: data/sessions/{session_id}.json
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button(
                    "📚 履歴ページで確認", key="view_history", use_container_width=True
                ):
                    st.switch_page("pages/history.py")
            with col2:
                if st.button(
                    "🔄 新しいアドバイスを生成", key="new_advice", use_container_width=True
                ):
                    st.session_state.pre_advice_form_data = {}
                    st.session_state.pop("pre_advice_session_id", None)
                    st.rerun()
            with col3:
                download_data = {
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "type": "pre_advice",
                    "input": sales_input.dict(),
                    "output": {
                        "advice": advice,
                        "selected_icebreaker": st.session_state.get(
                            "selected_icebreaker"
                        ),
                    },
                }
                json_str = json.dumps(download_data, ensure_ascii=False, indent=2)
                st.download_button(
                    label="📥 JSONダウンロード",
                    data=json_str,
                    file_name=f"pre_advice_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key="download_button",
                    use_container_width=True,
                )

            st.info(
                "💡 **次のステップ**: 履歴ページで保存されたセッションを確認したり、新しいアドバイスを生成したりできます。"
            )
        except Exception as e:
            st.error(f"❌ 保存に失敗しました: {str(e)}")
            st.info(
                "しばらく時間をおいて再度お試しください。問題が続く場合は管理者にお問い合わせください。"
            )
