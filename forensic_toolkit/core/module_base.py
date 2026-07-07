"""
Module 基类与注册机制。

每个取证模块继承 ModuleBase，设置元信息并实现 run() 方法。
通过 @ModuleRegistry.register 装饰器或继承自动注册。

注册后的模块可通过 CLI 自动发现。
"""

from __future__ import annotations
import abc
from dataclasses import dataclass, field
from typing import Any, ClassVar

from forensic_toolkit.core.types import ForensicError


@dataclass
class ModuleMeta:
    """模块的声明式元信息。"""
    name: str                                  # 命令行子命令名 (snake_case)
    description: str                           # 一句话描述
    author: str = "Forensic Toolkit"           # 作者
    version: str = "0.1.0"                     # 模块版本
    supported_platforms: tuple[str, ...] = ()  # 空 = 全平台
    requires_admin: bool = False               # 是否需要 root/管理员
    output_formats: tuple[str, ...] = ("table", "json", "csv")


class ModuleBase(abc.ABC):
    """所有取证模块的抽象基类。"""

    meta: ClassVar[ModuleMeta]

    def __init__(self, **kwargs: Any) -> None:
        self.params = kwargs

    @abc.abstractmethod
    def run(self) -> Any:
        """执行取证任务，返回结构化结果。"""
        ...

    def validate(self) -> None:
        """运行前的参数/环境校验。"""
        if self.meta.requires_admin:
            from forensic_toolkit.core.platform import Platform
            Platform.require_admin()
        if self.meta.supported_platforms:
            from forensic_toolkit.core.platform import Platform
            Platform.require_platform(*self.meta.supported_platforms)


class ModuleRegistry:
    """全局模块注册表。"""

    _modules: dict[str, type[ModuleBase]] = {}

    @classmethod
    def register(cls, module_cls: type[ModuleBase]) -> type[ModuleBase]:
        name = module_cls.meta.name
        if name in cls._modules:
            raise ForensicError(f"模块名重复: {name}")
        cls._modules[name] = module_cls
        return module_cls

    @classmethod
    def get(cls, name: str) -> type[ModuleBase]:
        if name not in cls._modules:
            raise ForensicError(f"未知模块: {name}")
        return cls._modules[name]

    @classmethod
    def list(cls) -> list[ModuleMeta]:
        return [m.meta for m in cls._modules.values()]

    @classmethod
    def names(cls) -> list[str]:
        return list(cls._modules.keys())
