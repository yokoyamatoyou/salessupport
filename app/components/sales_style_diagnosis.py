"""
営業スタイル診断コンポーネント
営業パーソンが自分の営業スタイルを簡単に診断できるUIを提供
"""
import streamlit as st
from core.models import SalesStyle
from typing import Dict, List, Optional
from translations import t


class SalesStyleDiagnosis:
    """営業スタイル診断クラス"""

    def __init__(self):
        self.questions = self._get_diagnosis_questions()

    def _get_diagnosis_questions(self) -> List[Dict]:
        """診断質問を取得"""
        return [
            {
                "id": "q1",
                "question": "商談で最も重視するのは何ですか？",
                "options": [
                    {
                        "text": "相手との信頼関係を築くこと",
                        "style": SalesStyle.RELATIONSHIP_BUILDER,
                        "points": 3
                    },
                    {
                        "text": "相手の課題を解決すること",
                        "style": SalesStyle.PROBLEM_SOLVER,
                        "points": 3
                    },
                    {
                        "text": "自社の強みを効果的に伝えること",
                        "style": SalesStyle.VALUE_PROPOSER,
                        "points": 3
                    },
                    {
                        "text": "専門的なアドバイスを提供すること",
                        "style": SalesStyle.SPECIALIST,
                        "points": 3
                    },
                    {
                        "text": "確実に契約を獲得すること",
                        "style": SalesStyle.DEAL_CLOSER,
                        "points": 3
                    }
                ]
            },
            {
                "id": "q2",
                "question": "商談中のあなたの話し方を表すと？",
                "options": [
                    {
                        "text": "相手の話をじっくり聞いて共感を示す",
                        "style": SalesStyle.RELATIONSHIP_BUILDER,
                        "points": 2
                    },
                    {
                        "text": "論理的に課題を整理して解決策を提案する",
                        "style": SalesStyle.PROBLEM_SOLVER,
                        "points": 2
                    },
                    {
                        "text": "自社の強みを具体的に数字や事例で示す",
                        "style": SalesStyle.VALUE_PROPOSER,
                        "points": 2
                    },
                    {
                        "text": "業界の専門知識を活かしてアドバイスする",
                        "style": SalesStyle.SPECIALIST,
                        "points": 2
                    },
                    {
                        "text": "価格交渉や条件面を積極的に進める",
                        "style": SalesStyle.DEAL_CLOSER,
                        "points": 2
                    }
                ]
            },
            {
                "id": "q3",
                "question": "商談後のフォローアップで重視するのは？",
                "options": [
                    {
                        "text": "定期的な関係維持と情報提供",
                        "style": SalesStyle.RELATIONSHIP_BUILDER,
                        "points": 2
                    },
                    {
                        "text": "課題解決のための継続的なサポート",
                        "style": SalesStyle.PROBLEM_SOLVER,
                        "points": 2
                    },
                    {
                        "text": "自社製品・サービスの価値再確認",
                        "style": SalesStyle.VALUE_PROPOSER,
                        "points": 2
                    },
                    {
                        "text": "専門的な知見の継続的な提供",
                        "style": SalesStyle.SPECIALIST,
                        "points": 2
                    },
                    {
                        "text": "契約に向けた最終的なクロージング",
                        "style": SalesStyle.DEAL_CLOSER,
                        "points": 2
                    }
                ]
            }
        ]

    def get_style_info(self, style: SalesStyle) -> Dict:
        """営業スタイルの詳細情報を取得"""
        style_info = {
            SalesStyle.RELATIONSHIP_BUILDER: {
                "name": "🤝 関係構築型",
                "description": "相手との信頼関係を大切にし、中長期的な関係構築を重視します",
                "strengths": ["人間関係の構築", "信頼獲得", "長期的な関係維持"],
                "advice_style": "共感を重視した柔らかいトーン",
                "icebreaker_focus": "パーソナルな話題から始める"
            },
            SalesStyle.PROBLEM_SOLVER: {
                "name": "🧩 課題解決型",
                "description": "相手の課題を的確に把握し、最適な解決策を提案します",
                "strengths": ["課題分析", "解決策提案", "論理的思考"],
                "advice_style": "論理的で構造化された説明",
                "icebreaker_focus": "相手の状況を理解する質問から始める"
            },
            SalesStyle.VALUE_PROPOSER: {
                "name": "💎 価値提案型",
                "description": "自社の強みを効果的に伝え、相手にとっての価値を明確化します",
                "strengths": ["価値訴求", "強み発信", "説得力のある提案"],
                "advice_style": "具体的な数字や事例を交えた説明",
                "icebreaker_focus": "自社の強みを自然に織り交ぜる"
            },
            SalesStyle.SPECIALIST: {
                "name": "🧭 専門家型",
                "description": "業界・専門知識を活かし、信頼できるアドバイザーとして対応します",
                "strengths": ["専門知識", "信頼性向上", "アドバイザー的役割"],
                "advice_style": "専門用語を交えた詳細な説明",
                "icebreaker_focus": "業界知識を活かした話題から始める"
            },
            SalesStyle.DEAL_CLOSER: {
                "name": "🎯 成約志向型",
                "description": "目標達成を重視し、効率的に商談を進め契約獲得を目指します",
                "strengths": ["目標達成", "効率性", "クロージング力"],
                "advice_style": "簡潔で行動喚起を促す表現",
                "icebreaker_focus": "商談の目的を明確にした話題から始める"
            }
        }
        return style_info.get(style, {})

    def diagnose_style(self, answers: Dict[str, SalesStyle]) -> SalesStyle:
        """回答から営業スタイルを診断"""
        scores = {}

        for answer in answers.values():
            if answer in scores:
                scores[answer] += 1
            else:
                scores[answer] = 1

        # 最も多く選ばれたスタイルを返す
        return max(scores, key=scores.get)

    def render_diagnosis_ui(self) -> Optional[SalesStyle]:
        """診断UIを描画"""
        st.markdown("### 🎯 あなたの営業スタイル診断")

        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            text-align: center;
            color: white;
        ">
            <h3 style="margin: 0; color: white;">営業スタイルを診断しましょう</h3>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">
                3つの質問に答えるだけで、あなたの営業スタイルがわかります
            </p>
        </div>
        """, unsafe_allow_html=True)

        # セッション状態の初期化
        if "diagnosis_step" not in st.session_state:
            st.session_state.diagnosis_step = 0
        if "diagnosis_answers" not in st.session_state:
            st.session_state.diagnosis_answers = {}

        current_step = st.session_state.diagnosis_step

        if current_step < len(self.questions):
            # 診断中のUI
            question = self.questions[current_step]

            st.markdown(f"#### 質問 {current_step + 1}/3")
            st.markdown(f"**{question['question']}**")

            # オプションを表示
            for i, option in enumerate(question['options']):
                if st.button(
                    option['text'],
                    key=f"option_{current_step}_{i}",
                    use_container_width=True,
                    type="secondary"
                ):
                    st.session_state.diagnosis_answers[question['id']] = option['style']
                    st.session_state.diagnosis_step += 1
                    st.rerun()

            # プログレスバー
            progress = (current_step + 1) / len(self.questions)
            st.progress(progress)

        else:
            # 診断完了
            diagnosed_style = self.diagnose_style(st.session_state.diagnosis_answers)

            st.success("🎉 診断が完了しました！")

            style_info = self.get_style_info(diagnosed_style)

            st.markdown("### あなたの営業スタイル")
            st.markdown(f"## {style_info['name']}")
            st.markdown(f"**{style_info['description']}**")

            # 強みを表示
            st.markdown("#### 💪 あなたの強み")
            for strength in style_info['strengths']:
                st.markdown(f"• {strength}")

            # アドバイススタイルを表示
            st.markdown("#### 💬 アドバイススタイル")
            st.markdown(style_info['advice_style'])

            # アイスブレイカーの特徴を表示
            st.markdown("#### ❄️ アイスブレイクの特徴")
            st.markdown(style_info['icebreaker_focus'])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ このスタイルで進む", type="primary", use_container_width=True):
                    return diagnosed_style

            with col2:
                if st.button("🔄 もう一度診断する", use_container_width=True):
                    st.session_state.diagnosis_step = 0
                    st.session_state.diagnosis_answers = {}
                    st.rerun()

        return None

    def render_style_selector_fallback(self) -> Optional[SalesStyle]:
        """診断が不要な場合の直接選択UI"""
        st.markdown("### 🎯 営業スタイルを選択")

        st.markdown("すでにご自分の営業スタイルがわかっている場合は、直接選択してください。")

        style_options = []
        for style in SalesStyle:
            info = self.get_style_info(style)
            style_options.append(f"{info['name']} - {info['description'][:50]}...")

        selected_index = st.selectbox(
            "営業スタイルを選択してください：",
            range(len(style_options)),
            format_func=lambda x: style_options[x],
            key="style_selector"
        )

        if st.button("✅ このスタイルを選択", type="primary"):
            return list(SalesStyle)[selected_index]

        return None
