"""
セキュリティユーティリティモジュール
プロンプトインジェクション対策とセキュリティ強化のための機能を提供
"""
import re
import hashlib
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class SanitizeResult:
    """サニタイズ結果"""
    text: str
    is_safe: bool
    warnings: List[str]


@dataclass
class PromptAnalysis:
    """プロンプト分析結果"""
    content: str
    token_count: int
    risk_level: str  # 'low', 'medium', 'high'
    detected_patterns: List[str]


class PromptSecurityManager:
    """プロンプトセキュリティマネージャー"""

    # 危険なパターンの定義
    DANGEROUS_PATTERNS = [
        (r'(?i)\b(?:system|assistant|user|developer)\s*:', 'role_marker', 'high'),
        (r'<script[^>]*>.*?</script>', 'script_tag', 'high'),
        (r'<[^>]+>', 'html_tag', 'medium'),
        (r'```\w*\n.*?```', 'code_block', 'medium'),
        (r'`.*?`', 'inline_code', 'low'),
        (r'\{\{.*?\}\}', 'template_var', 'low'),
        (r'\$\{.*?\}', 'variable_expansion', 'medium'),
        (r'(?i)\b(?:ignore|override|forget)\s+(?:previous|all|these)?\s+(?:instructions?|rules?)', 'instruction_override', 'high'),
        (r'(?i)\b(?:you\s+are|act\s+as)\s+a\s+.*?(?:ai|assistant|model)', 'role_change', 'high'),
    ]

    @classmethod
    def sanitize_input(cls, text: str, max_length: int = 10000) -> SanitizeResult:
        """
        高度なプロンプトサニタイズ

        Args:
            text: サニタイズ対象のテキスト
            max_length: 最大許容長

        Returns:
            SanitizeResult: サニタイズ結果
        """
        if not isinstance(text, str):
            return SanitizeResult(str(text), False, ["非文字列入力"])

        warnings = []
        original_text = text

        # 長さチェック
        if len(text) > max_length:
            text = text[:max_length]
            warnings.append(f"テキストが{max_length}文字を超えたため切り詰めました")

        # 危険パターンの検出と除去
        for pattern, description, risk in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                warnings.append(f"危険パターン検出: {description} (リスク: {risk})")
                if risk in ['high', 'medium']:
                    text = re.sub(pattern, '[FILTERED]', text, flags=re.IGNORECASE | re.DOTALL)

        # 特殊文字の制限的エスケープ
        text = re.sub(r'[\\\'\"`]', '', text)

        # 制御文字の除去
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

        # 連続する空白の正規化
        text = re.sub(r'\s+', ' ', text)

        # 安全性の評価
        is_safe = len([w for w in warnings if 'リスク: high' in w]) == 0 and len(text) <= max_length

        return SanitizeResult(text.strip(), is_safe, warnings)

    @classmethod
    def analyze_prompt(cls, prompt: str) -> PromptAnalysis:
        """
        プロンプトの詳細分析

        Args:
            prompt: 分析対象のプロンプト

        Returns:
            PromptAnalysis: 分析結果
        """
        detected_patterns = []
        risk_score = 0

        for pattern, description, risk in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE | re.DOTALL):
                detected_patterns.append(description)
                if risk == 'high':
                    risk_score += 3
                elif risk == 'medium':
                    risk_score += 2
                else:
                    risk_score += 1

        # リスクレベルの決定
        if risk_score >= 5:
            risk_level = 'high'
        elif risk_score >= 2:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        return PromptAnalysis(
            content=prompt,
            token_count=cls._estimate_token_count(prompt),
            risk_level=risk_level,
            detected_patterns=detected_patterns
        )

    @classmethod
    def validate_prompt_length(cls, prompt: str, max_tokens: int = 8000) -> bool:
        """プロンプト長をトークン数で検証"""
        estimated_tokens = cls._estimate_token_count(prompt)
        return estimated_tokens <= max_tokens

    @staticmethod
    def _estimate_token_count(text: str) -> int:
        """テキストのトークン数を推定（改善版）"""
        if not text:
            return 0

        # 日本語文字のカウント
        japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', text))

        # 英語単語のカウント
        english_words = len(re.findall(r'\b\w+\b', text))

        # 記号・数字のカウント
        symbols = len(re.findall(r'[^\w\s\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', text))

        # 日本語は1文字=1トークン、英語は単語数、記号は0.5トークンとして計算
        total_tokens = japanese_chars + english_words + int(symbols * 0.5)

        return max(total_tokens, 1)  # 最低1トークン

    @staticmethod
    def generate_prompt_hash(prompt: str, mode: str, schema: Optional[Dict[str, Any]] = None) -> str:
        """プロンプトのハッシュを生成（キャッシュ用）"""
        content = f"{prompt}|{mode}|{json.dumps(schema, sort_keys=True) if schema else ''}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @classmethod
    def escape_for_template(cls, text: str) -> str:
        """テンプレート用の高度なエスケープ"""
        if not isinstance(text, str):
            return str(text)

        # 波括弧のエスケープ
        text = text.replace("{", "{{").replace("}", "}}")

        # テンプレート変数の保護
        text = re.sub(r'\$\$(\w+)', r'$\1', text)  # $$var を $var に戻す

        return text


class TokenTracker:
    """トークン使用量追跡クラス"""

    def __init__(self):
        self.usage_history: List[Dict[str, Any]] = []

    def track_usage(self, response: Any, user_id: str) -> Dict[str, int]:
        """応答のトークン使用量を追跡"""
        usage = getattr(response, "usage", None)
        if not usage:
            return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

        token_usage = {
            "input_tokens": getattr(usage, "prompt_tokens", 0),
            "output_tokens": getattr(usage, "completion_tokens", 0),
            "total_tokens": getattr(usage, "total_tokens", 0)
        }

        # 使用履歴の記録
        self.usage_history.append({
            "user_id": user_id,
            "timestamp": None,  # 実際にはdatetime.now()を使用
            "usage": token_usage
        })

        return token_usage

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """ユーザーのトークン使用統計を取得"""
        user_history = [h for h in self.usage_history if h["user_id"] == user_id]

        if not user_history:
            return {"total_tokens": 0, "session_count": 0, "avg_tokens_per_session": 0}

        total_tokens = sum(h["usage"]["total_tokens"] for h in user_history)
        session_count = len(user_history)
        avg_tokens = total_tokens / session_count if session_count > 0 else 0

        return {
            "total_tokens": total_tokens,
            "session_count": session_count,
            "avg_tokens_per_session": avg_tokens
        }
