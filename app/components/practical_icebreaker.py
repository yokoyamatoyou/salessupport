"""
実践的なアイスブレイク生成コンポーネント
営業スタイルに基づいた現場で使える自然な表現を生成
"""
import random
from typing import List, Dict, Any, Optional
from core.models import SalesStyle
from services.logger import Logger


logger = Logger("PracticalIcebreaker")


class PracticalIcebreakerGenerator:
    """実践的なアイスブレイク生成クラス"""

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """営業スタイル別のテンプレートを読み込み"""

        return {
            SalesStyle.RELATIONSHIP_BUILDER.value: {
                "general": [
                    "お時間をいただきありがとうございます。{company}の事業について、ぜひお聞かせいただけますか？",
                    "この度はご連絡をいただきありがとうございます。{company}の現在の取り組みについて教えていただけますか？",
                    "いつもお世話になっております。{company}の今後の展望についてお聞かせいただけますか？",
                    "{industry}業界のトレンドについて、どのようにお考えでしょうか？",
                ],
                "problem_focused": [
                    "{company}の現在の事業課題について、お聞かせいただけますか？",
                    "デジタル化の取り組みについて、どのようなお考えをお持ちでしょうか？",
                    "{industry}業界における競争環境について、どのように分析されていますか？",
                ],
                "relationship_building": [
                    "{company}とのお付き合いは何年になりますか？これからもよろしくお願いいたします。",
                    "前回のお打ち合わせから、どのような変化がありましたか？",
                    "今後の事業展開について、ぜひお聞かせください。",
                ]
            },

            SalesStyle.PROBLEM_SOLVER.value: {
                "general": [
                    "{company}の事業課題について、ぜひ詳しくお聞かせいただけますか？",
                    "{industry}業界における課題解決について、お考えを共有していただけますか？",
                    "現在の事業環境について、どのような課題を感じていらっしゃいますか？",
                ],
                "analytical": [
                    "{company}の事業KPIについて、どのように評価されていますか？",
                    "市場環境の変化に対して、どのような対策を検討されていますか？",
                    "{industry}業界の将来展望について、どのように分析されていますか？",
                ],
                "solution_oriented": [
                    "課題解決のための取り組みについて、お聞かせいただけますか？",
                    "事業改善のための具体的な施策について、ご相談させていただけますか？",
                ]
            },

            SalesStyle.VALUE_PROPOSER.value: {
                "general": [
                    "{company}の強みを活かした取り組みについて、お聞かせいただけますか？",
                    "貴社の価値創造について、ぜひ詳しくお聞かせください。",
                    "{company}の競争優位性について、どのようにお考えでしょうか？",
                ],
                "value_focused": [
                    "貴社の強みをさらに強化するための取り組みについて、ご相談させていただけますか？",
                    "{company}の独自の価値提案について、お聞かせいただけますか？",
                    "市場での差別化戦略について、どのようなお考えをお持ちでしょうか？",
                ],
                "benefit_oriented": [
                    "貴社の事業成長のためのパートナーシップについて、ご検討いただけますか？",
                    "{company}の将来価値について、一緒に考えさせていただけますか？",
                ]
            },

            SalesStyle.SPECIALIST.value: {
                "general": [
                    "{industry}業界の専門的な知見について、お聞かせいただけますか？",
                    "{company}の技術戦略について、ぜひ詳しくお聞かせください。",
                    "業界トレンドに対する{company}の取り組みについて、お考えを共有していただけますか？",
                ],
                "expertise_focused": [
                    "{industry}業界の最新動向について、どのように分析されていますか？",
                    "{company}の技術的な課題について、ご相談させていただけますか？",
                    "専門的な視点から見た{industry}業界の将来について、お聞かせいただけますか？",
                ],
                "consultative": [
                    "{company}の事業戦略について、アドバイスさせていただけますか？",
                    "専門家の視点から、{company}の強みについて分析させていただけますか？",
                ]
            },

            SalesStyle.DEAL_CLOSER.value: {
                "general": [
                    "{company}の事業目標について、ぜひお聞かせいただけますか？",
                    "この度の商談について、どのような成果を目指されていますか？",
                    "{company}の投資計画について、お聞かせいただけますか？",
                ],
                "goal_oriented": [
                    "貴社の事業目標達成のためのパートナーとして、ご検討いただけますか？",
                    "{company}の成長戦略について、一緒に具体的な計画を立てさせていただけますか？",
                    "この商談を通じて、どのような成果を実現したいと考えていらっしゃいますか？",
                ],
                "action_focused": [
                    "次のステップについて、具体的に検討させていただけますか？",
                    "{company}の決定プロセスについて、お聞かせいただけますか？",
                ]
            }
        }

    def generate_practical_icebreakers(
        self,
        sales_style: SalesStyle,
        industry: str,
        company_hint: Optional[str] = None,
        count: int = 3
    ) -> List[str]:
        """
        実践的なアイスブレイクを生成

        Args:
            sales_style: 営業スタイル
            industry: 業界
            company_hint: 会社に関するヒント
            count: 生成する数

        Returns:
            生成されたアイスブレイクのリスト
        """
        try:
            style_templates = self.templates.get(sales_style.value, {})
            if not style_templates:
                return self._generate_fallback_icebreakers(industry, count)

            # テンプレートのカテゴリからランダムに選択
            all_templates = []
            for category, templates in style_templates.items():
                all_templates.extend(templates)

            if not all_templates:
                return self._generate_fallback_icebreakers(industry, count)

            # 会社情報を活用
            company_name = self._extract_company_name(company_hint) if company_hint else industry + "企業"

            # 指定数だけ生成（重複なし）
            selected_templates = random.sample(all_templates, min(count, len(all_templates)))

            icebreakers = []
            for template in selected_templates:
                icebreaker = template.format(
                    company=company_name,
                    industry=industry
                )
                icebreakers.append(icebreaker)

            logger.info(f"Generated {len(icebreakers)} practical icebreakers for {sales_style.value}")
            return icebreakers

        except Exception as e:
            logger.error(f"Error generating practical icebreakers: {e}")
            return self._generate_fallback_icebreakers(industry, count)

    def _extract_company_name(self, company_hint: str) -> str:
        """会社ヒントから会社名を抽出"""
        if not company_hint:
            return "貴社"

        # 一般的な会社名パターンを抽出
        import re

        # 「株式会社○○」や「○○株式会社」パターン
        company_patterns = [
            r'(株式会社[^\s,，。]+)',
            r'([^\s,，。]+株式会社)',
            r'([^\s,，。]+有限会社)',
            r'([^\s,，。]+合同会社)',
        ]

        for pattern in company_patterns:
            match = re.search(pattern, company_hint)
            if match:
                return match.group(1)

        # 会社名として使えそうな単語を抽出
        words = re.findall(r'[^\s,，。]+', company_hint)
        if words:
            # 最も長い単語を会社名として使用
            return max(words, key=len)

        return "貴社"

    def _generate_fallback_icebreakers(self, industry: str, count: int) -> List[str]:
        """フォールバック用のアイスブレイク生成"""
        fallbacks = [
            f"{industry}業界の最新トレンドについて、お聞かせいただけますか？",
            f"貴社の{industry}分野での取り組みについて、ぜひお聞かせください。",
            f"{industry}業界における課題について、お考えを共有していただけますか？",
            f"貴社の{industry}事業について、詳しくお聞かせいただけますか？",
            f"{industry}業界の将来展望について、どのようにお考えでしょうか？",
        ]

        return random.sample(fallbacks, min(count, len(fallbacks)))

    def get_style_specific_tips(self, sales_style: SalesStyle) -> Dict[str, Any]:
        """営業スタイル別の使用Tipsを取得"""

        tips = {
            SalesStyle.RELATIONSHIP_BUILDER: {
                "tone": "柔らかく共感を示す",
                "focus": "相手の話を引き出す",
                "follow_up": "関係性を深める質問",
                "examples": [
                    "前回のお打ち合わせから変化はありましたか？",
                    "今後の事業展開についてお聞かせいただけますか？"
                ]
            },
            SalesStyle.PROBLEM_SOLVER: {
                "tone": "論理的で建設的",
                "focus": "課題の明確化",
                "follow_up": "解決策の提案",
                "examples": [
                    "現在の課題を具体的に教えていただけますか？",
                    "どのような解決策を検討されていますか？"
                ]
            },
            SalesStyle.VALUE_PROPOSER: {
                "tone": "自信を持って価値を伝える",
                "focus": "自社の強みの訴求",
                "follow_up": "具体的な価値提案",
                "examples": [
                    "貴社の強みをさらに強化する方法について",
                    "当社の強みを活かしたご提案について"
                ]
            },
            SalesStyle.SPECIALIST: {
                "tone": "専門性を持って信頼性を示す",
                "focus": "専門知識の提供",
                "follow_up": "専門的なアドバイス",
                "examples": [
                    "業界トレンドについての見解",
                    "専門的な課題解決のアプローチ"
                ]
            },
            SalesStyle.DEAL_CLOSER: {
                "tone": "目的志向で行動喚起",
                "focus": "次のステップの明確化",
                "follow_up": "具体的なアクション",
                "examples": [
                    "次のミーティングの日程について",
                    "契約に向けた具体的な検討事項"
                ]
            }
        }

        return tips.get(sales_style, {
            "tone": "自然で相手に合わせる",
            "focus": "相手の話を引き出す",
            "follow_up": "関係性を深める",
            "examples": ["現在の状況についてお聞かせいただけますか？"]
        })

    def generate_contextual_icebreaker(
        self,
        sales_style: SalesStyle,
        industry: str,
        company_hint: Optional[str] = None,
        meeting_context: Optional[str] = None
    ) -> str:
        """
        文脈を考慮したアイスブレイクを生成

        Args:
            sales_style: 営業スタイル
            industry: 業界
            company_hint: 会社ヒント
            meeting_context: ミーティングの文脈

        Returns:
            文脈を考慮したアイスブレイク
        """
        base_icebreakers = self.generate_practical_icebreakers(
            sales_style, industry, company_hint, count=5
        )

        if not meeting_context:
            return random.choice(base_icebreakers)

        # 文脈に応じた調整
        context_keywords = {
            "初回": ["はじめまして", "初めまして", "初めて"],
            "フォロー": ["前回", "前回の続き", "フォローアップ"],
            "提案": ["ご提案", "提案内容", "ソリューション"],
            "クロージング": ["最終確認", "契約", "決定"],
        }

        for context_type, keywords in context_keywords.items():
            if any(keyword in meeting_context for keyword in keywords):
                return self._adjust_for_context(base_icebreakers[0], context_type)

        return base_icebreakers[0]

    def _adjust_for_context(self, icebreaker: str, context: str) -> str:
        """文脈に応じてアイスブレイクを調整"""
        adjustments = {
            "初回": "改めまして、よろしくお願いいたします。",
            "フォロー": "前回のお打ち合わせの続きとなりますが、",
            "提案": "本日は具体的なご提案についてお話ししますが、",
            "クロージング": "最終的なご検討についてお聞かせいただけますか？"
        }

        adjustment = adjustments.get(context, "")
        if adjustment:
            return f"{adjustment} {icebreaker}"

        return icebreaker
