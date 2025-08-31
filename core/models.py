from enum import Enum
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator, HttpUrl

# 従来の9種類の営業タイプ（後方互換性のため維持）
class SalesType(str, Enum):
    HUNTER = "hunter"  # 🏹 ハンター
    CLOSER = "closer"  # 🔒 クローザー
    RELATION = "relation"  # 🤝 リレーション
    CONSULTANT = "consultant"  # 🧭 コンサル
    CHALLENGER = "challenger"  # ⚡ チャレンジャー
    STORYTELLER = "storyteller"  # 📖 ストーリーテラー
    ANALYST = "analyst"  # 📊 アナリスト
    PROBLEM_SOLVER = "problem_solver"  # 🧩 問題解決
    FARMER = "farmer"  # 🌾 ファーマー

# 新しい実践的な営業スタイル（5種類）
class SalesStyle(str, Enum):
    RELATIONSHIP_BUILDER = "relationship_builder"  # 🤝 関係構築型
    PROBLEM_SOLVER = "problem_solver"             # 🧩 課題解決型
    VALUE_PROPOSER = "value_proposer"             # 💎 価値提案型
    SPECIALIST = "specialist"                     # 🧭 専門家型
    DEAL_CLOSER = "deal_closer"                   # 🎯 成約志向型

class LLMMode(str, Enum):
    SPEED = "speed"
    DEEP = "deep"
    CREATIVE = "creative"

class SearchProvider(str, Enum):
    NONE = "none"
    CSE = "cse"
    NEWSAPI = "newsapi"
    STUB = "stub"
    HYBRID = "hybrid"

class AppSettings(BaseModel):
    """アプリケーション設定"""
    # LLM設定
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAIモデル名")
    default_llm_mode: LLMMode = Field(default=LLMMode.SPEED, description="デフォルトのLLMモード")
    max_tokens: int = Field(default=1000, ge=100, le=4000, description="最大トークン数")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="創造性（温度）")
    
    # 検索設定
    search_provider: SearchProvider = Field(default=SearchProvider.STUB, description="検索プロバイダー")
    search_results_limit: int = Field(default=5, ge=1, le=20, description="検索結果の最大件数")
    search_trusted_domains: List[str] = Field(default_factory=lambda: [
        "www.bloomberg.co.jp", "www.nikkei.com", "www.itmedia.co.jp", "www.impress.co.jp"
    ], description="信頼ドメインのホワイトリスト")
    search_time_window_days: int = Field(default=60, ge=1, le=365, description="新鮮度評価に使う日数")
    search_language: str = Field(default="ja", description="検索言語（newsapi等）")
    
    # UI設定
    language: str = Field(default="ja", description="言語設定")
    theme: str = Field(default="light", description="テーマ設定")
    show_tutorial_on_start: bool = Field(default=True, description="起動時にチュートリアルを表示")
    
    # データ設定
    data_dir: str = Field(default="./data", description="データ保存ディレクトリ")
    auto_save: bool = Field(default=True, description="自動保存の有効/無効")

    # CRM設定
    crm_enabled: bool = Field(default=False, description="CRM連携の有効/無効")
    
    # カスタマイズ設定
    custom_prompts: Dict[str, str] = Field(default_factory=dict, description="カスタムプロンプト")
    sales_type_colors: Dict[str, str] = Field(default_factory=dict, description="営業タイプ別の色設定")

    @field_validator("search_provider", mode="before")
    @classmethod
    def _validate_search_provider(cls, v: Any) -> SearchProvider:
        """検索プロバイダーの値を検証し、不正値はSTUBにフォールバック"""
        if isinstance(v, SearchProvider):
            return v
        try:
            return SearchProvider(str(v))
        except Exception:
            return SearchProvider.STUB

class SalesInput(BaseModel):
    sales_type: SalesType
    industry: str
    product: str
    description: Optional[str] = None
    description_url: HttpUrl | None = None
    competitor: Optional[str] = None
    competitor_url: HttpUrl | None = None
    stage: str
    purpose: str
    constraints: List[str] = Field(default_factory=list)

class PreAdviceOutput(BaseModel):
    short_term: dict
    mid_term: dict

class PostReviewOutput(BaseModel):
    summary: str
    bant: dict
    champ: dict
    objections: List[dict]
    risks: List[dict]
    next_actions: List[str]
    followup_email: dict
    metrics_update: dict

