#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器模块

负责管理系统配置，支持动态更新配置参数，确保系统配置的一致性和可维护性。
"""

from typing import Dict, List, Any, Optional
import json
import os
import threading
import copy


class ConfigManager:
    """
    配置管理器类
    """
    
    # 敏感配置的环境变量覆盖表：配置路径 -> 候选环境变量名（按顺序取第一个非空的）
    # 对应 config/config.json.example 里的占位符，说明见根目录 .env.example
    ENV_OVERRIDES = (
        (("neo4j", "uri"), ("NEO4J_URI",)),
        (("neo4j", "username"), ("NEO4J_USER", "NEO4J_USERNAME")),
        (("neo4j", "password"), ("NEO4J_PASSWORD",)),
        (("neo4j", "database"), ("NEO4J_DATABASE",)),
        (("redis", "url"), ("REDIS_URL",)),
        (("context_manager", "redis", "url"), ("REDIS_URL",)),
        (("model_router", "main_model", "api_key"), ("DEEPSEEK_API_KEY",)),
        (("model_router", "assistant_model", "api_key"), ("DEEPSEEK_API_KEY",)),
    )

    def __init__(self, config_file: str = "config/config.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        # 尽力加载项目根目录的 .env（未安装 python-dotenv 时静默跳过）
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        # 配置文件路径
        self.config_file = config_file
        
        # 默认配置
        self.default_config = {
            "system": {
                "name": "智能科研选题助手",
                "version": "1.0.0",
                "description": "基于大模型的智能科研选题助手",
                "debug": False,
            },
            "core_agent": {
                "timeout": 30,
                "retry_count": 3,
            },
            "context_manager": {
                "max_history_length": 10,
                "max_context_depth": 5,
                "save_interval": 300,
                "context_file": "data/contexts/contexts.json",
                "auto_save": True,
                "auto_load": True,
                "auto_summarize": True,
                "summary_trigger_length": 10,
                "summary_keep_recent": 5,
                "max_summary_chars": 1200,
                "storage_backend": "redis",
                "redis": {
                    "url": "redis://localhost:6379/0",
                    "context_ttl_seconds": 86400,
                    "cache_ttl_seconds": 3600,
                },
            },
            "neo4j": {
                "uri": "bolt://localhost:7687",
                "username": "neo4j",
                "password": "your_neo4j_password",
                "database": "neo4j",
            },
            "redis": {
                "url": "redis://localhost:6379/0",
                "context_ttl_seconds": 86400,
                "cache_ttl_seconds": 3600,
            },
            "topic_recommendation": {
                "session_storage": "redis",
                "prefer_neo4j": True,
            },
            "model_router": {
                "main_model": {
                    "provider": "deepseek",
                    "api_key": "",
                    "model": "deepseek-chat",
                    "base_url": "https://api.deepseek.com/v1/chat/completions",
                },
                "assistant_model": {
                    "provider": "deepseek",
                    "api_key": "",
                    "model": "deepseek-chat",
                    "base_url": "https://api.deepseek.com/v1/chat/completions",
                },
                "timeout": 30,
                "retry_count": 3,
            },
            "document_retriever": {
                "document_dir": "data/documents",
                "index_file": "data/document_index.json",
                "max_results": 5,
                "min_similarity": 0.1,
                "auto_build_index": False,
                "supported_extensions": [".txt", ".md", ".json"],
            },
            "response_generator": {
                "max_response_length": 2048,
                "min_response_length": 10,
                "response_timeout": 30,
            },
            "error_handler": {
                "error_log_file": "data/error_log.json",
                "max_error_logs": 1000,
                "error_threshold": 10,
                "error_window": 60,
                "retry_delay": 1,
                "max_retries": 3,
            },
            "log_manager": {
                "log_dir": "data/logs",
                "log_file": "data/logs/agent.log",
                "log_level": "INFO",
                "log_rotation": "daily",
            },
        }
        
        # 当前配置
        self.config = copy.deepcopy(self.default_config)
        
        # 线程锁
        self.lock = threading.RLock()
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
    
    def load_config(self) -> bool:
        """
        加载配置
        
        Returns:
            是否加载成功
        """
        try:
            with self.lock:
                if os.path.exists(self.config_file):
                    with open(self.config_file, "r", encoding="utf-8") as f:
                        loaded_config = json.load(f)
                    
                    # 合并配置
                    self._merge_config(self.config, loaded_config)
                    
                    print(f"配置加载成功: {self.config_file}")
                    return True
                else:
                    # 配置文件不存在，使用默认配置并保存
                    self.save_config()
                    print(f"配置文件不存在，使用默认配置: {self.config_file}")
                    return False
        except Exception as e:
            print(f"加载配置失败: {str(e)}")
            # 加载失败，使用默认配置
            self.config = copy.deepcopy(self.default_config)
            return False
    
    def save_config(self) -> bool:
        """
        保存配置
        
        Returns:
            是否保存成功
        """
        try:
            with self.lock:
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
                
                print(f"配置保存成功: {self.config_file}")
                return True
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
            return False
    
    @classmethod
    def _apply_env_overrides(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        用环境变量覆盖敏感配置项（密钥 / 密码）
        
        优先级：环境变量 > 配置文件 > 默认值。这样 config.json 里只需要保留
        占位符（见 config/config.json.example），真实密钥通过 .env 或系统环境
        变量注入 —— 既不必写进文件，也就不会被误提交。
        
        注意：只在读取时覆盖，不写回 self.config，因此 save_config() 永远不会
        把环境变量里的密钥落盘。
        
        Args:
            config: 待覆盖的配置副本
            
        Returns:
            覆盖后的配置
        """
        for path, env_names in cls.ENV_OVERRIDES:
            value = None
            for name in env_names:
                value = os.environ.get(name)
                if value:
                    break
            if not value:
                continue
            
            node = config
            for key in path[:-1]:
                node = node.get(key)
                if not isinstance(node, dict):
                    node = None
                    break
            if isinstance(node, dict):
                node[path[-1]] = value
        return config
    
    def get_config(self, key: Optional[str] = None, default: Any = None) -> Any:
        """
        获取配置
        
        Args:
            key: 配置键，支持点号分隔的路径
            default: 默认值
            
        Returns:
            配置值
        """
        with self.lock:
            # 先应用环境变量覆盖（敏感项），再按 key 取值
            config = self._apply_env_overrides(copy.deepcopy(self.config))
            
            if key is None:
                return config
            
            # 解析键路径
            keys = key.split(".")
            value = config
            
            try:
                for k in keys:
                    value = value[k]
                return value
            except KeyError:
                return default
    
    def set_config(self, key: str, value: Any) -> bool:
        """
        设置配置
        
        Args:
            key: 配置键，支持点号分隔的路径
            value: 配置值
            
        Returns:
            是否设置成功
        """
        try:
            with self.lock:
                # 解析键路径
                keys = key.split(".")
                config = self.config
                
                # 遍历到倒数第二个键
                for k in keys[:-1]:
                    if k not in config:
                        config[k] = {}
                    config = config[k]
                
                # 设置值
                config[keys[-1]] = value
                
                print(f"配置更新成功: {key} = {value}")
                return True
        except Exception as e:
            print(f"设置配置失败: {str(e)}")
            return False
    
    def update_config(self, config: Dict[str, Any]) -> bool:
        """
        更新配置
        
        Args:
            config: 配置字典
            
        Returns:
            是否更新成功
        """
        try:
            with self.lock:
                # 合并配置
                self._merge_config(self.config, config)
                
                print("配置更新成功")
                return True
        except Exception as e:
            print(f"更新配置失败: {str(e)}")
            return False
    
    def reset_config(self) -> bool:
        """
        重置配置到默认值
        
        Returns:
            是否重置成功
        """
        try:
            with self.lock:
                self.config = copy.deepcopy(self.default_config)
                self.save_config()
                
                print("配置重置成功")
                return True
        except Exception as e:
            print(f"重置配置失败: {str(e)}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """
        验证配置
        
        Returns:
            验证结果
        """
        try:
            with self.lock:
                errors = []
                warnings = []
                
                # 验证模型配置（走 get_config，以便计入环境变量覆盖）
                if not self.get_config("model_router.main_model.api_key"):
                    warnings.append("主模型 API key 未设置")
                
                if not self.get_config("model_router.assistant_model.api_key"):
                    warnings.append("辅助模型 API key 未设置")
                
                # 验证路径
                for path_key in [
                    "context_manager.context_file",
                    "document_retriever.document_dir",
                    "document_retriever.index_file",
                    "error_handler.error_log_file",
                    "log_manager.log_file",
                ]:
                    path = self.get_config(path_key)
                    if path:
                        dir_path = os.path.dirname(path)
                        if dir_path:
                            os.makedirs(dir_path, exist_ok=True)
                
                return {
                    "valid": len(errors) == 0,
                    "errors": errors,
                    "warnings": warnings,
                }
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"验证配置失败: {str(e)}"],
                "warnings": [],
            }
    
    def _merge_config(self, target: Dict[str, Any], source: Dict[str, Any]):
        """
        合并配置
        
        Args:
            target: 目标配置
            source: 源配置
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_config(target[key], value)
            else:
                target[key] = value
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """
        获取模型配置
        
        Args:
            model_name: 模型名称，可选值：main_model, assistant_model
            
        Returns:
            模型配置
        """
        return self.get_config(f"model_router.{model_name}")
    
    def set_model_config(self, model_name: str, config: Dict[str, Any]) -> bool:
        """
        设置模型配置
        
        Args:
            model_name: 模型名称，可选值：main_model, assistant_model
            config: 模型配置
            
        Returns:
            是否设置成功
        """
        return self.update_config({"model_router": {model_name: config}})
    
    def get_document_config(self) -> Dict[str, Any]:
        """
        获取文档检索配置
        
        Returns:
            文档检索配置
        """
        return self.get_config("document_retriever")
    
    def set_document_config(self, config: Dict[str, Any]) -> bool:
        """
        设置文档检索配置
        
        Args:
            config: 文档检索配置
            
        Returns:
            是否设置成功
        """
        return self.update_config({"document_retriever": config})
    
    def get_context_config(self) -> Dict[str, Any]:
        """
        获取上下文管理配置
        
        Returns:
            上下文管理配置
        """
        return self.get_config("context_manager")
    
    def set_context_config(self, config: Dict[str, Any]) -> bool:
        """
        设置上下文管理配置
        
        Args:
            config: 上下文管理配置
            
        Returns:
            是否设置成功
        """
        return self.update_config({"context_manager": config})
