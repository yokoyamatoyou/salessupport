"""
依存性注入コンテナ
サービス間の疎結合とテスト容易性を向上
"""
from typing import Dict, Any, Type, TypeVar, Optional, Callable
from abc import ABC, abstractmethod
import threading
from services.logger import Logger


T = TypeVar('T')
logger = Logger("DIContainer")


class ServiceLifetime:
    """サービスのライフタイム"""
    TRANSIENT = "transient"  # 毎回新しいインスタンス
    SCOPED = "scoped"       # スコープ内でのシングルトン
    SINGLETON = "singleton" # アプリケーション全体でのシングルトン


class ServiceDescriptor:
    """サービス記述子"""

    def __init__(self, service_type: Type[T], implementation: Type[T] = None,
                 factory: Callable = None, lifetime: str = ServiceLifetime.TRANSIENT):
        self.service_type = service_type
        self.implementation = implementation or service_type
        self.factory = factory
        self.lifetime = lifetime


class IServiceProvider(ABC):
    """サービスプロバイダーインターフェース"""

    @abstractmethod
    def get_service(self, service_type: Type[T]) -> T:
        pass

    @abstractmethod
    def get_service_optional(self, service_type: Type[T]) -> Optional[T]:
        pass


class ServiceCollection:
    """サービスコレクション"""

    def __init__(self):
        self._descriptors: Dict[Type, ServiceDescriptor] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self._singleton_instances: Dict[Type, Any] = {}

    def add_transient(self, service_type: Type[T], implementation: Type[T] = None) -> None:
        """一時サービスの登録"""
        descriptor = ServiceDescriptor(service_type, implementation, lifetime=ServiceLifetime.TRANSIENT)
        self._descriptors[service_type] = descriptor

    def add_scoped(self, service_type: Type[T], implementation: Type[T] = None) -> None:
        """スコープサービスの登録"""
        descriptor = ServiceDescriptor(service_type, implementation, lifetime=ServiceLifetime.SCOPED)
        self._descriptors[service_type] = descriptor

    def add_singleton(self, service_type: Type[T], implementation: Type[T] = None, instance: Any = None) -> None:
        """シングルトンサービスの登録"""
        if instance is not None:
            self._singleton_instances[service_type] = instance
            return

        descriptor = ServiceDescriptor(service_type, implementation, lifetime=ServiceLifetime.SINGLETON)
        self._descriptors[service_type] = descriptor

    def add_factory(self, service_type: Type[T], factory: Callable[[], T],
                   lifetime: str = ServiceLifetime.TRANSIENT) -> None:
        """ファクトリを使用したサービスの登録"""
        descriptor = ServiceDescriptor(service_type, factory=factory, lifetime=lifetime)
        self._descriptors[service_type] = descriptor

    def get_descriptor(self, service_type: Type[T]) -> Optional[ServiceDescriptor]:
        """サービス記述子の取得"""
        return self._descriptors.get(service_type)


class ServiceProvider(IServiceProvider):
    """サービスプロバイダー実装"""

    def __init__(self, collection: ServiceCollection):
        self.collection = collection
        self._scoped_instances: Dict[Type, Any] = {}
        self._lock = threading.Lock()

    def get_service(self, service_type: Type[T]) -> T:
        """サービスの取得（必須）"""
        service = self.get_service_optional(service_type)
        if service is None:
            raise ValueError(f"Service not registered: {service_type}")
        return service

    def get_service_optional(self, service_type: Type[T]) -> Optional[T]:
        """サービスの取得（オプション）"""
        descriptor = self.collection.get_descriptor(service_type)
        if not descriptor:
            return None

        with self._lock:
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                if service_type not in self.collection._singleton_instances:
                    self.collection._singleton_instances[service_type] = self._create_instance(descriptor)
                return self.collection._singleton_instances[service_type]

            elif descriptor.lifetime == ServiceLifetime.SCOPED:
                if service_type not in self._scoped_instances:
                    self._scoped_instances[service_type] = self._create_instance(descriptor)
                return self._scoped_instances[service_type]

            else:  # TRANSIENT
                return self._create_instance(descriptor)

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """インスタンスの作成"""
        if descriptor.factory:
            return descriptor.factory()
        else:
            return descriptor.implementation()

    def create_scope(self) -> 'ServiceProvider':
        """新しいスコープの作成"""
        return ServiceProvider(self.collection)


class ServiceLocator:
    """サービスロケーター（グローバルアクセス用）"""

    _instance: Optional[ServiceProvider] = None
    _lock = threading.Lock()

    @classmethod
    def configure(cls, provider: ServiceProvider) -> None:
        """サービスプロバイダーの設定"""
        with cls._lock:
            cls._instance = provider
            logger.info("Service locator configured")

    @classmethod
    def get_service(cls, service_type: Type[T]) -> T:
        """サービスの取得"""
        if cls._instance is None:
            raise RuntimeError("Service locator is not configured")
        return cls._instance.get_service(service_type)

    @classmethod
    def get_service_optional(cls, service_type: Type[T]) -> Optional[T]:
        """サービスの取得（オプション）"""
        if cls._instance is None:
            return None
        return cls._instance.get_service_optional(service_type)


# デフォルトのサービスコレクションとプロバイダー
_default_collection = ServiceCollection()
_default_provider = ServiceProvider(_default_collection)


def configure_services() -> None:
    """デフォルトサービスの設定"""
    from services.prompt_manager import EnhancedPromptManager
    from services.schema_manager import UnifiedSchemaManager
    from services.security_utils import PromptSecurityManager
    from providers.llm_openai import EnhancedOpenAIProvider
    from services.usage_meter import UsageMeter
    from services.settings_manager import SettingsManager
    from providers.search_provider import WebSearchProvider
    from services.search_enhancer import SearchEnhancerService

    # LLMプロバイダー
    _default_collection.add_factory(
        EnhancedOpenAIProvider,
        lambda: EnhancedOpenAIProvider(),
        lifetime=ServiceLifetime.SINGLETON,
    )

    # プロンプトマネージャー
    _default_collection.add_factory(
        EnhancedPromptManager,
        lambda: EnhancedPromptManager(),
        lifetime=ServiceLifetime.SINGLETON,
    )

    # スキーママネージャー
    _default_collection.add_factory(
        UnifiedSchemaManager,
        lambda: UnifiedSchemaManager(),
        lifetime=ServiceLifetime.SINGLETON,
    )

    # セキュリティマネージャー
    _default_collection.add_factory(
        PromptSecurityManager,
        lambda: PromptSecurityManager(),
        lifetime=ServiceLifetime.SINGLETON,
    )

    # ユーセージメーター
    _default_collection.add_singleton(
        UsageMeter,
        instance=UsageMeter()
    )

    # 設定マネージャー
    _default_collection.add_singleton(
        SettingsManager,
        instance=SettingsManager()
    )

    # Web検索プロバイダー
    _default_collection.add_factory(
        WebSearchProvider,
        lambda: WebSearchProvider(_default_provider.get_service(SettingsManager)),
        lifetime=ServiceLifetime.SINGLETON,
    )

    # 検索高度化サービス
    _default_collection.add_factory(
        SearchEnhancerService,
        lambda: SearchEnhancerService(
            _default_provider.get_service(SettingsManager),
            _default_provider.get_service_optional(EnhancedOpenAIProvider),
            _default_provider.get_service(WebSearchProvider),
        ),
        lifetime=ServiceLifetime.SINGLETON,
    )

    # サービスロケーターの設定
    ServiceLocator.configure(_default_provider)
    logger.info("Default services configured")


def get_service(service_type: Type[T]) -> T:
    """グローバルサービス取得関数"""
    return ServiceLocator.get_service(service_type)


def get_service_optional(service_type: Type[T]) -> Optional[T]:
    """グローバルサービス取得関数（オプション）"""
    return ServiceLocator.get_service_optional(service_type)


# 初期化
configure_services()
