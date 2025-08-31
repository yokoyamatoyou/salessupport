"""
スマートデフォルト設定コンポーネント
営業スタイルに基づいてフォームのデフォルト値を自動設定
"""
from typing import Dict, Any, Optional, List
from core.models import SalesStyle
from services.logger import Logger


logger = Logger("SmartDefaults")


class SmartDefaultsManager:
    """スマートデフォルト設定マネージャー"""

    def __init__(self):
        self.defaults_config = self._load_defaults_config()

    def _load_defaults_config(self) -> Dict[str, Dict[str, Any]]:
        """営業スタイル別のデフォルト設定を読み込み"""

        return {
            SalesStyle.RELATIONSHIP_BUILDER.value: {
                "purpose": "長期的な関係構築と信頼獲得",
                "constraints": ["関係構築を優先", "長期的な視点で検討"],
                "industry_focus": "サービス業中心",
                "communication_style": "柔らかく共感を重視",
                "follow_up_style": "定期的な関係維持",
                "icebreaker_tone": "フレンドリー",
                "meeting_context": "関係構築",
                "kpi_focus": "関係継続率"
            },

            SalesStyle.PROBLEM_SOLVER.value: {
                "purpose": "顧客課題の特定と解決策の提案",
                "constraints": ["課題解決を優先", "技術的な実現可能性を考慮"],
                "industry_focus": "製造業・IT中心",
                "communication_style": "論理的で構造化された説明",
                "follow_up_style": "課題解決の継続サポート",
                "icebreaker_tone": "プロフェッショナル",
                "meeting_context": "課題分析",
                "kpi_focus": "解決満足度"
            },

            SalesStyle.VALUE_PROPOSER.value: {
                "purpose": "自社製品・サービスの価値を効果的に伝える",
                "constraints": ["競合優位性を明確に", "投資対効果を考慮"],
                "industry_focus": "全業界対応",
                "communication_style": "具体的な数字・事例を交えた説明",
                "follow_up_style": "価値再確認とフォロー",
                "icebreaker_tone": "自信を持って",
                "meeting_context": "価値提案",
                "kpi_focus": "受注単価"
            },

            SalesStyle.SPECIALIST.value: {
                "purpose": "専門知識を活かしたアドバイス提供",
                "constraints": ["専門性の維持", "最新情報の活用"],
                "industry_focus": "専門性が高い業界",
                "communication_style": "専門用語を交えた詳細な説明",
                "follow_up_style": "専門的な継続支援",
                "icebreaker_tone": "専門性アピール",
                "meeting_context": "専門相談",
                "kpi_focus": "専門性評価"
            },

            SalesStyle.DEAL_CLOSER.value: {
                "purpose": "効率的に商談を進め契約獲得を目指す",
                "constraints": ["契約獲得を優先", "リスク最小化"],
                "industry_focus": "全業界対応",
                "communication_style": "簡潔で行動喚起を促す表現",
                "follow_up_style": "契約に向けたクロージング",
                "icebreaker_tone": "目的志向",
                "meeting_context": "クロージング",
                "kpi_focus": "受注率"
            }
        }

    def get_smart_defaults(self, sales_style: SalesStyle, industry: str = "") -> Dict[str, Any]:
        """
        営業スタイルと業界に基づいてスマートデフォルトを取得

        Args:
            sales_style: 営業スタイル
            industry: 業界（オプション）

        Returns:
            スマートデフォルト設定
        """
        try:
            base_defaults = self.defaults_config.get(sales_style.value, {})

            # 業界固有の調整
            industry_adjustments = self._get_industry_adjustments(industry)
            defaults = {**base_defaults, **industry_adjustments}

            logger.info(f"Generated smart defaults for {sales_style.value} in {industry}")
            return defaults

        except Exception as e:
            logger.error(f"Error generating smart defaults: {e}")
            return {}

    def _get_industry_adjustments(self, industry: str) -> Dict[str, Any]:
        """業界固有の調整を取得"""

        industry_configs = {
            "IT": {
                "purpose": "デジタル化の課題解決と最新技術の活用",
                "constraints": ["技術トレンドの考慮", "セキュリティ要件の確認"],
                "communication_style": "技術的な詳細を交えた説明"
            },
            "製造業": {
                "purpose": "生産性向上と品質管理の改善",
                "constraints": ["既存設備への適合性", "導入コストの最適化"],
                "communication_style": "具体的な数値目標を交えた説明"
            },
            "金融": {
                "purpose": "リスク管理と業務効率化の両立",
                "constraints": ["規制遵守", "セキュリティ基準の確保"],
                "communication_style": "リスクとリターンをバランスよく説明"
            },
            "医療": {
                "purpose": "患者ケアの質向上と業務効率化",
                "constraints": ["医療規制の遵守", "患者プライバシーの保護"],
                "communication_style": "信頼性と倫理的配慮を重視した説明"
            },
            "小売": {
                "purpose": "顧客体験の向上と売上最適化",
                "constraints": ["顧客満足度の維持", "競争力の確保"],
                "communication_style": "顧客視点での価値提案"
            }
        }

        # 部分一致で業界設定を探す
        for key, config in industry_configs.items():
            if key in industry:
                return config

        return {}

    def suggest_constraints(self, sales_style: SalesStyle, industry: str = "") -> List[str]:
        """制約事項の提案"""
        defaults = self.get_smart_defaults(sales_style, industry)
        base_constraints = defaults.get("constraints", [])

        # 業界固有の追加制約
        industry_specific = {
            "IT": ["システム統合の可能性", "データ移行の影響"],
            "製造業": ["生産ラインへの影響", "トレーニング期間"],
            "金融": ["コンプライアンス要件", "監査対応"],
            "医療": ["医療機器認証", "運用ワークフロー変更"],
            "小売": ["店舗運営への影響", "顧客対応フロー変更"]
        }

        for key, constraints in industry_specific.items():
            if key in industry:
                base_constraints.extend(constraints)
                break

        return list(set(base_constraints))  # 重複除去

    def suggest_purpose_examples(self, sales_style: SalesStyle, industry: str = "") -> List[str]:
        """目的の例を提案"""
        base_purpose = self.get_smart_defaults(sales_style, industry).get("purpose", "")

        # 業界固有の目的例
        industry_examples = {
            "IT": [
                "デジタルトランスフォーメーションの実現",
                "業務プロセスの自動化と効率化",
                "データ活用による意思決定の改善"
            ],
            "製造業": [
                "生産性の向上とコスト削減",
                "品質管理システムの強化",
                "サプライチェーンの最適化"
            ],
            "金融": [
                "リスク管理体制の強化",
                "顧客サービスの向上",
                "業務効率化とコンプライアンス強化"
            ]
        }

        examples = [base_purpose] if base_purpose else []

        for key, ex_list in industry_examples.items():
            if key in industry:
                examples.extend(ex_list)
                break

        return examples[:5]  # 最大5つに制限

    def get_recommended_meeting_context(self, sales_style: SalesStyle) -> str:
        """推奨されるミーティング文脈を取得"""
        defaults = self.get_smart_defaults(sales_style)
        return defaults.get("meeting_context", "初回商談")

    def get_communication_tips(self, sales_style: SalesStyle) -> Dict[str, str]:
        """コミュニケーションTipsを取得"""
        defaults = self.get_smart_defaults(sales_style)

        return {
            "tone": defaults.get("communication_style", "自然で相手に合わせる"),
            "icebreaker_tone": defaults.get("icebreaker_tone", "フレンドリー"),
            "follow_up": defaults.get("follow_up_style", "継続的な関係維持")
        }

    def validate_form_data(self, form_data: Dict[str, Any], sales_style: SalesStyle) -> Dict[str, List[str]]:
        """
        フォームデータをスマートデフォルトで検証

        Args:
            form_data: フォームデータ
            sales_style: 営業スタイル

        Returns:
            検証結果（提案と警告）
        """
        defaults = self.get_smart_defaults(sales_style)
        suggestions = []
        warnings = []

        # 目的の検証
        if not form_data.get("purpose"):
            suggestions.append(f"目的例: {defaults.get('purpose', '商談の目的を明確に設定しましょう')}")

        # 制約の検証
        constraints = form_data.get("constraints", [])
        if not constraints:
            default_constraints = defaults.get("constraints", [])
            if default_constraints:
                suggestions.append(f"制約例: {', '.join(default_constraints[:2])}")

        # 業界適合性の検証
        industry = form_data.get("industry", "")
        if industry and defaults.get("industry_focus"):
            if defaults["industry_focus"] not in industry and industry not in defaults["industry_focus"]:
                warnings.append(f"{industry}業界では{defaults['industry_focus']}の経験が有効です")

        return {
            "suggestions": suggestions,
            "warnings": warnings
        }


def apply_smart_defaults_to_form(form_data: Dict[str, Any], sales_style: SalesStyle,
                                industry: str = "") -> Dict[str, Any]:
    """
    フォームにスマートデフォルトを適用

    Args:
        form_data: 現在のフォームデータ
        sales_style: 営業スタイル
        industry: 業界

    Returns:
        更新されたフォームデータ
    """
    manager = SmartDefaultsManager()
    defaults = manager.get_smart_defaults(sales_style, industry)

    updated_data = form_data.copy()

    # 空のフィールドにデフォルト値を適用
    for key, value in defaults.items():
        if key in updated_data and not updated_data[key]:
            if isinstance(value, list):
                updated_data[key] = value[0] if value else ""
            else:
                updated_data[key] = value

    return updated_data
