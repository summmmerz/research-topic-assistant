#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础模块

提供公共的基类和工具函数
"""

from typing import Dict, List, Any, Optional
import threading


class BaseModule:
    """
    基础模块类
    
    提供所有模块的公共初始化逻辑
    """
    
    def __init__(self, config: Dict[str, Any], error_handler: Any, logger: Any):
        """
        初始化基础模块
        
        Args:
            config: 配置参数
            error_handler: 错误处理器
            logger: 日志记录器
        """
        self.config = config
        self.error_handler = error_handler
        self.logger = logger
        self.lock = threading.RLock()
    
    def initialize(self):
        """
        初始化模块
        """
        pass
    
    def shutdown(self):
        """
        关闭模块
        """
        pass
    
    def update_config(self, config: Dict[str, Any]):
        """
        更新配置
        
        Args:
            config: 新配置
        """
        with self.lock:
            self.config.update(config)
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取状态
        
        Returns:
            状态信息
        """
        return {
            "config": self.config,
        }


def merge_config(default_config: Dict[str, Any], user_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并配置
    
    Args:
        default_config: 默认配置
        user_config: 用户配置
        
    Returns:
        合并后的配置
    """
    merged = default_config.copy()
    merged.update(user_config)
    return merged


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    安全获取字典值
    
    Args:
        data: 字典数据
        key: 键
        default: 默认值
        
    Returns:
        值或默认值
    """
    return data.get(key, default)
