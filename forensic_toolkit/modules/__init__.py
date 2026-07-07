"""取证模块注册入口 - 各模块在顶部 import 即可自注册到 ModuleRegistry"""
from forensic_toolkit.core.module_base import ModuleRegistry

# 注册所有模块（延迟导入，只在需要时加载）
_registry = ModuleRegistry()

def discover():
    """惰性发现所有模块"""
    return _registry

__all__ = ["discover", "_registry"]
