import yaml
from typing import List, Dict, Any
from string import Template
from core.models import SalesType
from providers.llm_openai import OpenAIProvider
from providers.search_provider import WebSearchProvider
from services.utils import escape_braces, sanitize_for_prompt

class IcebreakerService:
    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager
        # プロンプトは先に読み込んでおく（APIキー未設定でもUIが動くようにする）
        self.prompt_template = self._load_prompt_template()
        # LLMプロバイダはキー未設定時にフォールバックさせる
        try:
            self.llm_provider = OpenAIProvider(settings_manager)
        except Exception:
            self.llm_provider = None
        # 検索プロバイダは常に生成（provider=noneのときは空配列を返す）
        self.search_provider = WebSearchProvider(settings_manager)
        # 直近の検索結果（UI表示用）
        self.last_news_items: list[dict] = []
    
    def _load_prompt_template(self) -> Dict[str, Any]:
        """プロンプトテンプレートを読み込み"""
        try:
            with open("prompts/icebreaker.yaml", "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError("プロンプトファイル 'prompts/icebreaker.yaml' が見つかりません")
    
    def generate_icebreakers(self, sales_type: SalesType, industry: str, company_hint: str = None, search_enabled: bool = True) -> List[str]:
        """アイスブレイクを生成"""
        try:
            # 業界ニュースを取得
            news_items = []
            if search_enabled:
                news_items = self.search_provider.search(f"{industry} 最新ニュース", 2)
            # UI表示用に保持
            self.last_news_items = news_items or []
            
            # トーン辞書を取得
            tone = self._get_tone_for_type(sales_type)
            
            # プロンプトを構築
            prompt = self._build_prompt(sales_type, industry, company_hint, news_items, tone)
            
            # LLMで生成（プロバイダがない場合は例外→フォールバック）
            response = self.llm_provider.call_llm(
                prompt, "creative", self._get_icebreaker_schema()
            ) if self.llm_provider else None
            
            # レスポンスからアイスブレイクを抽出
            if isinstance(response, dict) and "icebreakers" in response:
                return response["icebreakers"]
            else:
                # フォールバック: レスポンスが期待される形式でない場合
                return self._generate_fallback_icebreakers(sales_type, industry, tone)
                
        except Exception as e:
            # エラーが発生した場合はフォールバックを使用
            tone = self._get_tone_for_type(sales_type)
            # 検索結果はリセット
            self.last_news_items = []
            return self._generate_fallback_icebreakers(sales_type, industry, tone)
    
    def _get_tone_for_type(self, sales_type: SalesType) -> str:
        """営業タイプに応じたトーンを取得"""
        tones = {
            SalesType.HUNTER: "前向き・短文・行動促進",
            SalesType.CLOSER: "価値訴求→締めの一言",
            SalesType.RELATION: "共感・近況・柔らかめ",
            SalesType.CONSULTANT: "課題仮説・問いかけ",
            SalesType.CHALLENGER: "仮説提示・視点転換",
            SalesType.STORYTELLER: "具体例・物語",
            SalesType.ANALYST: "事実・データ起点",
            SalesType.PROBLEM_SOLVER: "障害除去・次の一歩",
            SalesType.FARMER: "長期関係・紹介喚起"
        }
        return tones.get(sales_type, "一般的")
    
    def _build_prompt(self, sales_type: SalesType, industry: str, company_hint: str, news_items: List[Dict], tone: str) -> str:
        """プロンプトを構築"""
        # システムメッセージ
        system_msg = self.prompt_template["system"]

        # 業界ニュースの詳細を文字列として構築
        news_details = ""
        if news_items:
            news_details = "\n".join(
                [
                    f"- {escape_braces(sanitize_for_prompt(item['title']))}: {escape_braces(sanitize_for_prompt(item['snippet']))}"
                    for item in news_items
                ]
            )
            news_details = sanitize_for_prompt(news_details)

        # ユーザーメッセージ
        user_template = Template(self.prompt_template["user_template"])
        user_msg = user_template.safe_substitute(
            sales_type=escape_braces(sanitize_for_prompt(sales_type.value)),
            tone=escape_braces(sanitize_for_prompt(tone)),
            industry=escape_braces(sanitize_for_prompt(industry)),
            company_hint=escape_braces(sanitize_for_prompt(company_hint or 'なし')),
            news_items=escape_braces(sanitize_for_prompt(news_details)),
        )

        # 出力制約
        output_constraints = "\n".join(self.prompt_template["output_constraints"])

        # 完全なプロンプトを構築
        full_prompt = f"""
{system_msg}

{user_msg}

出力制約:
{output_constraints}

上記の情報を基に、{tone}のトーンで1行のアイスブレイクを3つ生成してください。
各アイスブレイクは自然で親しみやすく、商談の導入として適切な内容にしてください。
"""

        return full_prompt.replace("{{", "{").replace("}}", "}")
    
    def _generate_fallback_icebreakers(self, sales_type: SalesType, industry: str, tone: str) -> List[str]:
        """フォールバック用のアイスブレイクを生成"""
        # 営業タイプと業界に応じた基本的なアイスブレイク
        # "お聞かせください" is the correct polite phrase. Avoid the typo "お聞かください".
        fallback_templates = {
            SalesType.HUNTER: [
                f"最近の{industry}業界の動向はいかがですか？",
                f"{industry}で注目しているトレンドはありますか？",
                f"業界の変化について、どのように感じていますか？"
            ],
            SalesType.CLOSER: [
                f"{industry}業界での課題解決について、お聞かせください。",
                f"業界の効率化について、どのようなお考えですか？",
                f"競合他社との差別化について、どのようにお考えですか？"
            ],
            SalesType.RELATION: [
                f"お忙しい中、お時間をいただきありがとうございます。",
                f"最近の{industry}業界の状況はいかがでしょうか？",
                f"業界の変化について、どのようにお感じになっていますか？"
            ],
            SalesType.CONSULTANT: [
                f"{industry}業界で直面している課題について、お聞かせください。",
                f"業界の効率性向上について、どのようなお考えですか？",
                f"競合他社との差別化について、どのようなお考えですか？"
            ],
            SalesType.CHALLENGER: [
                f"{industry}業界の従来のアプローチに疑問を感じていませんか？",
                f"業界の常識を覆すような新しい視点について、どうお考えですか？",
                f"競合他社とは異なるアプローチについて、どのようにお考えですか？"
            ],
            SalesType.STORYTELLER: [
                f"最近、{industry}業界で印象に残った出来事はありますか？",
                f"業界の変化について、どのようなストーリーをお持ちですか？",
                f"競合他社との差別化について、どのようなお考えですか？"
            ],
            SalesType.ANALYST: [
                f"{industry}業界のデータ分析について、どのようにお考えですか？",
                f"業界の効率性指標について、どのようにお考えですか？",
                f"競合他社との差別化について、どのようにお考えですか？"
            ],
            SalesType.PROBLEM_SOLVER: [
                f"{industry}業界で解決したい課題について、お聞かせください。",
                f"業界の効率性向上について、どのようなお考えですか？",
                f"競合他社との差別化について、どのようにお考えですか？"
            ],
            SalesType.FARMER: [
                f"長期的な{industry}業界の展望について、どのようにお考えですか？",
                f"業界での人脈構築について、どのようにお考えですか？",
                f"競合他社との差別化について、どのようにお考えですか？"
            ]
        }
        
        return fallback_templates.get(sales_type, [
            f"最近の{industry}業界の動向はいかがですか？",
            f"{industry}で注目しているトレンドはありますか？",
            f"業界の変化について、どのように感じていますか？"
        ])
    
    def _get_icebreaker_schema(self) -> Dict[str, Any]:
        """アイスブレイク出力のJSONスキーマ"""
        return {
            "type": "object",
            "properties": {
                "icebreakers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 3
                }
            },
            "required": ["icebreakers"]
        }

