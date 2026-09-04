"""
AI Clients Module

统一管理所有 AI 提供商的客户端。
"""

from .UnifiedClient import UnifiedAIClient
from .EuropePMCClient import EuropePMCClient
# from .AIModelProvider import (
#     PROVIDER_REGISTRY,
#     ProviderConfig,
#     get_available_providers,
#     get_provider_config,
# )
from .AIPrompts import (
    APIKeyManager,
    ClientPrompts,
    BaseClient,
)

__all__ = [
    # 统一客户端
    "UnifiedAIClient",
    # Europe PMC 客户端
    "EuropePMCClient",
    # 核心组件
    "APIKeyManager",
    "ClientPrompts",
    "BaseClient",
]
