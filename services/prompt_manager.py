"""
強化されたプロンプト管理システム
セキュリティ、テンプレート管理、動的生成機能を備えたプロンプト管理
"""
import os
import yaml
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from string import Template
from abc import ABC, abstractmethod

from services.logger import Logger
from services.error_handler import ConfigurationError
from services.security_utils import PromptSecurityManager


logger = Logger("PromptManager")


@dataclass
class PromptTemplate:
    """プロンプトテンプレート"""
    name: str
    system_message: str
    user_template: str
    output_schema: Optional[Dict[str, Any]] = None
    constraints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"


@dataclass
class PromptContext:
    """プロンプト実行コンテキスト"""
    template_name: str
    variables: Dict[str, Any]
    mode: str = "speed"
    user_id: str = "default"
    sanitize: bool = True
    validate_length: bool = True


@dataclass
class RenderedPrompt:
    """レンダリングされたプロンプト"""
    system_message: str
    user_message: str
    full_prompt: str
    context: PromptContext
    security_analysis: Optional[Dict[str, Any]] = None
    token_estimate: int = 0


class PromptStorageInterface(ABC):
    """プロンプトストレージインターフェース"""

    @abstractmethod
    def load_template(self, name: str) -> Optional[PromptTemplate]:
        pass

    @abstractmethod
    def save_template(self, template: PromptTemplate) -> None:
        pass

    @abstractmethod
    def list_templates(self) -> List[str]:
        pass

    @abstractmethod
    def exists(self, name: str) -> bool:
        pass


class FileBasedPromptStorage(PromptStorageInterface):
    """ファイルベースのプロンプトストレージ"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_all_templates()

    def _load_all_templates(self):
        """全てのテンプレートを読み込み"""
        if not self.base_path.exists():
            logger.warning(f"Prompt directory not found: {self.base_path}")
            return

        for yaml_file in self.base_path.glob("*.yaml"):
            try:
                self._load_template_from_file(yaml_file)
            except Exception as e:
                logger.error(f"Failed to load template {yaml_file}: {e}")

    def _load_template_from_file(self, file_path: Path):
        """ファイルからテンプレートを読み込み"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        template = PromptTemplate(
            name=file_path.stem,
            system_message=data.get('system', ''),
            user_template=data.get('user', ''),
            output_schema=data.get('output_schema'),
            constraints=data.get('constraints', []),
            metadata=data.get('metadata', {}),
            version=data.get('version', '1.0.0')
        )

        self.templates[template.name] = template
        logger.info(f"Loaded prompt template: {template.name}")

    def load_template(self, name: str) -> Optional[PromptTemplate]:
        return self.templates.get(name)

    def save_template(self, template: PromptTemplate) -> None:
        file_path = self.base_path / f"{template.name}.yaml"

        data = {
            'system': template.system_message,
            'user': template.user_template,
            'version': template.version,
            'metadata': template.metadata,
            'constraints': template.constraints
        }

        if template.output_schema:
            data['output_schema'] = template.output_schema

        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

        self.templates[template.name] = template
        logger.info(f"Saved prompt template: {template.name}")

    def list_templates(self) -> List[str]:
        return list(self.templates.keys())

    def exists(self, name: str) -> bool:
        return name in self.templates


class EnhancedPromptManager:
    """強化されたプロンプトマネージャー"""

    def __init__(self, storage: Optional[PromptStorageInterface] = None):
        self.storage = storage or FileBasedPromptStorage(Path("prompts"))
        self.security_manager = PromptSecurityManager()
        self.template_cache: Dict[str, RenderedPrompt] = {}
        self.logger = Logger("EnhancedPromptManager")

    def render_prompt(self, context: PromptContext) -> RenderedPrompt:
        """
        プロンプトをレンダリング

        Args:
            context: プロンプト実行コンテキスト

        Returns:
            RenderedPrompt: レンダリングされたプロンプト
        """
        # テンプレート取得
        template = self.storage.load_template(context.template_name)
        if not template:
            raise ConfigurationError(f"Template not found: {context.template_name}")

        # 変数展開
        try:
            user_message = self._expand_variables(template.user_template, context.variables)
            system_message = self._expand_variables(template.system_message, context.variables)
        except KeyError as e:
            raise ConfigurationError(f"Missing required variable: {e}")

        # セキュリティチェック
        security_analysis = None
        if context.sanitize:
            analysis = self.security_manager.analyze_prompt(user_message)
            security_analysis = {
                'risk_level': analysis.risk_level,
                'detected_patterns': analysis.detected_patterns,
                'token_count': analysis.token_count
            }

            if analysis.risk_level == 'high':
                self.logger.warning(f"High risk prompt detected: {context.template_name}")

        # 長さ検証
        full_prompt = f"{system_message}\n\n{user_message}"
        token_estimate = self.security_manager._estimate_token_count(full_prompt)

        if context.validate_length and not self.security_manager.validate_prompt_length(full_prompt):
            raise ConfigurationError("Prompt too long for the model")

        rendered = RenderedPrompt(
            system_message=system_message,
            user_message=user_message,
            full_prompt=full_prompt,
            context=context,
            security_analysis=security_analysis,
            token_estimate=token_estimate
        )

        return rendered

    def _expand_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """変数を展開"""
        # セキュリティのため、変数をサニタイズ
        sanitized_vars = {}
        for key, value in variables.items():
            if isinstance(value, str):
                result = self.security_manager.sanitize_input(value)
                sanitized_vars[key] = result.text
            else:
                sanitized_vars[key] = str(value)

        # テンプレート展開
        try:
            expanded = Template(template).safe_substitute(sanitized_vars)
            return expanded
        except ValueError as e:
            raise ConfigurationError(f"Template expansion error: {e}")

    def create_template(self, template: PromptTemplate) -> None:
        """テンプレートを作成"""
        if self.storage.exists(template.name):
            raise ConfigurationError(f"Template already exists: {template.name}")

        self.storage.save_template(template)
        self.logger.info(f"Created template: {template.name}")

    def update_template(self, template: PromptTemplate) -> None:
        """テンプレートを更新"""
        if not self.storage.exists(template.name):
            raise ConfigurationError(f"Template not found: {template.name}")

        self.storage.save_template(template)
        self.logger.info(f"Updated template: {template.name}")

    def get_template_info(self, name: str) -> Optional[Dict[str, Any]]:
        """テンプレート情報を取得"""
        template = self.storage.load_template(name)
        if not template:
            return None

        return {
            'name': template.name,
            'version': template.version,
            'has_schema': template.output_schema is not None,
            'constraints': template.constraints,
            'metadata': template.metadata
        }

    def list_available_templates(self) -> List[Dict[str, Any]]:
        """利用可能なテンプレート一覧を取得"""
        templates = []
        for name in self.storage.list_templates():
            info = self.get_template_info(name)
            if info:
                templates.append(info)
        return templates

    def validate_template(self, template: PromptTemplate) -> List[str]:
        """テンプレートの妥当性を検証"""
        errors = []

        if not template.name:
            errors.append("Template name is required")

        if not template.system_message:
            errors.append("System message is required")

        if not template.user_template:
            errors.append("User template is required")

        # 必須変数のチェック
        try:
            # テンプレート内の変数を抽出
            import re
            vars_in_template = set(re.findall(r'\$\{([^}]+)\}', template.user_template + template.system_message))

            # サンプル変数でのテスト展開
            test_vars = {var: f"test_{var}" for var in vars_in_template}
            self._expand_variables(template.user_template, test_vars)
            self._expand_variables(template.system_message, test_vars)

        except Exception as e:
            errors.append(f"Template validation failed: {e}")

        return errors

    def get_template_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """テンプレートの出力スキーマを取得"""
        template = self.storage.load_template(name)
        return template.output_schema if template else None


# 後方互換性のための関数
def load_prompt_template() -> Dict[str, Any]:
    """古いインターフェースとの互換性維持"""
    manager = EnhancedPromptManager()
    # デフォルトのpre_adviceテンプレートを返す
    template = manager.storage.load_template("pre_advice")
    if template:
        return {
            'system': template.system_message,
            'user': template.user_template,
            'output_format': template.output_schema or {}
        }

    # フォールバック
    return {
        'system': 'あなたは日本のトップ営業コーチです。',
        'user': '営業タイプ: ${sales_type}\n業界: ${industry}\n...',
        'output_format': {}
    }
