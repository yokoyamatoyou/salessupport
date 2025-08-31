"""
統一されたスキーマ管理システム
JSONスキーマの生成、管理、検証を一元化
"""
import json
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod

from services.logger import Logger
from services.error_handler import ConfigurationError


logger = Logger("SchemaManager")


@dataclass
class SchemaDefinition:
    """スキーマ定義"""
    name: str
    version: str
    schema: Dict[str, Any]
    description: str = ""
    tags: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


class SchemaStorageInterface(ABC):
    """スキーマストレージインターフェース"""

    @abstractmethod
    def load_schema(self, name: str, version: Optional[str] = None) -> Optional[SchemaDefinition]:
        pass

    @abstractmethod
    def save_schema(self, schema_def: SchemaDefinition) -> None:
        pass

    @abstractmethod
    def list_schemas(self) -> List[str]:
        pass

    @abstractmethod
    def exists(self, name: str, version: Optional[str] = None) -> bool:
        pass


class FileBasedSchemaStorage(SchemaStorageInterface):
    """ファイルベースのスキーマストレージ"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.schemas: Dict[str, Dict[str, SchemaDefinition]] = {}
        self._load_all_schemas()

    def _load_all_schemas(self):
        """全てのスキーマを読み込み"""
        if not self.base_path.exists():
            self.base_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created schema directory: {self.base_path}")
            return

        for json_file in self.base_path.glob("*.json"):
            try:
                self._load_schema_from_file(json_file)
            except Exception as e:
                logger.error(f"Failed to load schema {json_file}: {e}")

    def _load_schema_from_file(self, file_path: Path):
        """ファイルからスキーマを読み込み"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        schema_def = SchemaDefinition(
            name=data['name'],
            version=data['version'],
            schema=data['schema'],
            description=data.get('description', ''),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )

        if schema_def.name not in self.schemas:
            self.schemas[schema_def.name] = {}

        self.schemas[schema_def.name][schema_def.version] = schema_def
        logger.info(f"Loaded schema: {schema_def.name} v{schema_def.version}")

    def load_schema(self, name: str, version: Optional[str] = None) -> Optional[SchemaDefinition]:
        if name not in self.schemas:
            return None

        versions = self.schemas[name]

        # バージョン指定がない場合は最新版を返す
        if version is None:
            latest_version = max(versions.keys())
            return versions[latest_version]

        return versions.get(version)

    def save_schema(self, schema_def: SchemaDefinition) -> None:
        file_name = f"{schema_def.name}_v{schema_def.version}.json"
        file_path = self.base_path / file_name

        data = {
            'name': schema_def.name,
            'version': schema_def.version,
            'schema': schema_def.schema,
            'description': schema_def.description,
            'tags': schema_def.tags,
            'metadata': schema_def.metadata
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        if schema_def.name not in self.schemas:
            self.schemas[schema_def.name] = {}

        self.schemas[schema_def.name][schema_def.version] = schema_def
        logger.info(f"Saved schema: {schema_def.name} v{schema_def.version}")

    def list_schemas(self) -> List[str]:
        return list(self.schemas.keys())

    def exists(self, name: str, version: Optional[str] = None) -> bool:
        if name not in self.schemas:
            return False

        if version is None:
            return len(self.schemas[name]) > 0

        return version in self.schemas[name]


class SchemaBuilder:
    """スキーマビルダー"""

    @staticmethod
    def create_pre_advice_schema() -> Dict[str, Any]:
        """事前アドバイス出力スキーマ生成"""
        return {
            "type": "object",
            "properties": {
                "short_term": {
                    "type": "object",
                    "properties": {
                        "openers": {
                            "type": "object",
                            "properties": {
                                "call": {"type": "string", "description": "電話での開幕スクリプト"},
                                "visit": {"type": "string", "description": "訪問時の開幕スクリプト"},
                                "email": {"type": "string", "description": "メールでの開幕スクリプト"}
                            },
                            "required": ["call", "visit", "email"]
                        },
                        "discovery": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "顧客の課題を深掘りする質問リスト"
                        },
                        "differentiation": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "vs": {"type": "string", "description": "競合名"},
                                    "talk": {"type": "string", "description": "差別化ポイントの説明"}
                                },
                                "required": ["vs", "talk"]
                            }
                        },
                        "objections": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string", "description": "反論タイプ（価格、機能など）"},
                                    "script": {"type": "string", "description": "対応スクリプト"}
                                },
                                "required": ["type", "script"]
                            }
                        },
                        "next_actions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "次の具体的なアクション"
                        },
                        "kpi": {
                            "type": "object",
                            "properties": {
                                "next_meeting_rate": {"type": "string", "description": "次の商談設定率目標"},
                                "poc_rate": {"type": "string", "description": "POC実施率目標"}
                            },
                            "required": ["next_meeting_rate", "poc_rate"]
                        },
                        "summary": {"type": "string", "description": "短期戦略の要約"}
                    },
                    "required": ["openers", "discovery", "differentiation", "objections", "next_actions", "kpi", "summary"]
                },
                "mid_term": {
                    "type": "object",
                    "properties": {
                        "plan_weeks_4_12": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "4-12週目の戦略的アクション"
                        }
                    },
                    "required": ["plan_weeks_4_12"]
                }
            },
            "required": ["short_term", "mid_term"]
        }

    @staticmethod
    def create_post_review_schema() -> Dict[str, Any]:
        """商談後ふりかえりスキーマ生成"""
        return {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "商談の要約（100-150文字）"},
                "bant": {
                    "type": "object",
                    "properties": {
                        "budget": {"type": "string", "description": "予算情報"},
                        "authority": {"type": "string", "description": "意思決定者情報"},
                        "need": {"type": "string", "description": "ニーズ・課題情報"},
                        "timeline": {"type": "string", "description": "タイムライン情報"}
                    },
                    "required": ["budget", "authority", "need", "timeline"]
                },
                "champ": {
                    "type": "object",
                    "properties": {
                        "challenges": {"type": "string", "description": "課題情報"},
                        "authority": {"type": "string", "description": "権限情報"},
                        "money": {"type": "string", "description": "予算情報"},
                        "prioritization": {"type": "string", "description": "優先度情報"}
                    },
                    "required": ["challenges", "authority", "money", "prioritization"]
                },
                "objections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "theme": {"type": "string", "description": "反論テーマ"},
                            "details": {"type": "string", "description": "反論詳細"},
                            "counter": {"type": "string", "description": "対応策"}
                        },
                        "required": ["theme", "details", "counter"]
                    }
                },
                "risks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "description": "リスク種類"},
                            "prob": {"type": "string", "description": "発生確率"},
                            "reason": {"type": "string", "description": "リスク理由"},
                            "mitigation": {"type": "string", "description": "軽減策"}
                        },
                        "required": ["type", "prob", "reason", "mitigation"]
                    }
                },
                "next_actions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "具体的な次のアクション"
                },
                "followup_email": {
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string", "description": "メール件名"},
                        "body": {"type": "string", "description": "メール本文"}
                    },
                    "required": ["subject", "body"]
                },
                "metrics_update": {
                    "type": "object",
                    "properties": {
                        "stage": {"type": "string", "description": "現在のステージ"},
                        "win_prob_delta": {"type": "string", "description": "勝率変化"}
                    },
                    "required": ["stage", "win_prob_delta"]
                }
            },
            "required": ["summary", "bant", "champ", "objections", "risks", "next_actions", "followup_email", "metrics_update"]
        }

    @staticmethod
    def create_icebreaker_schema() -> Dict[str, Any]:
        """アイスブレイカースキーマ生成"""
        return {
            "type": "object",
            "properties": {
                "icebreakers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "生成されたアイスブレイカー案",
                    "minItems": 3,
                    "maxItems": 5
                },
                "context": {
                    "type": "object",
                    "properties": {
                        "industry": {"type": "string"},
                        "company": {"type": "string"},
                        "sales_type": {"type": "string"}
                    }
                }
            },
            "required": ["icebreakers"]
        }


class UnifiedSchemaManager:
    """統一されたスキーママネージャー"""

    def __init__(self, storage: Optional[SchemaStorageInterface] = None):
        self.storage = storage or FileBasedSchemaStorage(Path("schemas"))
        self.builder = SchemaBuilder()
        self.logger = Logger("UnifiedSchemaManager")
        self._initialize_default_schemas()

    def _initialize_default_schemas(self):
        """デフォルトスキーマを初期化"""
        default_schemas = [
            ("pre_advice", "1.0.0", self.builder.create_pre_advice_schema(), "事前アドバイス出力スキーマ"),
            ("post_review", "1.0.0", self.builder.create_post_review_schema(), "商談後ふりかえりスキーマ"),
            ("icebreaker", "1.0.0", self.builder.create_icebreaker_schema(), "アイスブレイカースキーマ")
        ]

        for name, version, schema, description in default_schemas:
            if not self.storage.exists(name, version):
                schema_def = SchemaDefinition(
                    name=name,
                    version=version,
                    schema=schema,
                    description=description,
                    tags=["default", "system"]
                )
                try:
                    self.storage.save_schema(schema_def)
                    self.logger.info(f"Initialized default schema: {name}")
                except Exception as e:
                    self.logger.error(f"Failed to initialize schema {name}: {e}")

    def get_schema(self, name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """スキーマを取得"""
        schema_def = self.storage.load_schema(name, version)
        return schema_def.schema if schema_def else None

    def create_schema(self, name: str, schema: Dict[str, Any], version: str = "1.0.0",
                     description: str = "", tags: List[str] = None) -> None:
        """スキーマを作成"""
        if self.storage.exists(name, version):
            raise ConfigurationError(f"Schema already exists: {name} v{version}")

        schema_def = SchemaDefinition(
            name=name,
            version=version,
            schema=schema,
            description=description,
            tags=tags or []
        )

        self.storage.save_schema(schema_def)
        self.logger.info(f"Created schema: {name} v{version}")

    def update_schema(self, name: str, schema: Dict[str, Any], version: str,
                     description: Optional[str] = None) -> None:
        """スキーマを更新"""
        if not self.storage.exists(name):
            raise ConfigurationError(f"Schema not found: {name}")

        schema_def = SchemaDefinition(
            name=name,
            version=version,
            schema=schema,
            description=description or "",
            tags=["updated"]
        )

        self.storage.save_schema(schema_def)
        self.logger.info(f"Updated schema: {name} v{version}")

    def list_available_schemas(self) -> List[Dict[str, Any]]:
        """利用可能なスキーマ一覧を取得"""
        schemas = []
        for name in self.storage.list_schemas():
            schema_def = self.storage.load_schema(name)
            if schema_def:
                schemas.append({
                    'name': schema_def.name,
                    'version': schema_def.version,
                    'description': schema_def.description,
                    'tags': schema_def.tags
                })
        return schemas

    def validate_schema_definition(self, schema: Dict[str, Any]) -> List[str]:
        """スキーマ定義の妥当性を検証"""
        errors = []

        if not isinstance(schema, dict):
            errors.append("Schema must be a dictionary")
            return errors

        if 'type' not in schema:
            errors.append("Schema must have a 'type' field")

        # 基本的なJSON Schema検証
        if schema.get('type') not in ['object', 'array', 'string', 'number', 'boolean']:
            errors.append("Invalid schema type")

        return errors


# 後方互換性のための関数
def get_pre_advice_schema() -> Dict[str, Any]:
    """古いインターフェースとの互換性維持"""
    manager = UnifiedSchemaManager()
    return manager.get_schema("pre_advice") or SchemaBuilder.create_pre_advice_schema()


def get_post_review_schema() -> Dict[str, Any]:
    """古いインターフェースとの互換性維持"""
    manager = UnifiedSchemaManager()
    return manager.get_schema("post_review") or SchemaBuilder.create_post_review_schema()
