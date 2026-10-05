#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理器模块

负责记录系统运行日志
"""

from typing import Dict, List, Any, Optional
import threading
import os
import logging
import logging.handlers


class LogManager:
    """
    日志管理器类
    """
    
    def __init__(self, config: Dict):
        """
        初始化日志管理器
        
        Args:
            config: 配置参数
        """
        # 配置
        self.config = {
            "log_dir": config.get("log_dir", "data/logs"),
            "log_file": config.get("log_file", "data/logs/agent.log"),
            "log_level": config.get("log_level", "INFO"),
            "log_rotation": config.get("log_rotation", "daily"),
            "max_bytes": config.get("max_bytes", 10485760),  # 10MB
            "backup_count": config.get("backup_count", 7),
        }
        
        # 日志记录器
        self.logger = None
        
        # 线程锁
        self.lock = threading.RLock()
        
        # 确保目录存在
        os.makedirs(self.config["log_dir"], exist_ok=True)
        os.makedirs(os.path.dirname(self.config["log_file"]), exist_ok=True)
    
    def initialize(self):
        """
        初始化日志管理器
        """
        with self.lock:
            # 创建日志记录器
            self.logger = logging.getLogger("AgentLogger")
            self.logger.setLevel(self._get_log_level(self.config["log_level"]))
            
            # 清除已有的处理器
            self.logger.handlers = []
            
            # 创建文件处理器
            file_handler = self._create_file_handler()
            self.logger.addHandler(file_handler)
            
            # 创建控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self._get_log_level(self.config["log_level"]))
            console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            
            # 禁用其他日志记录器
            self._disable_other_loggers()
            
            self.logger.info("日志管理器初始化完成")
    
    def _create_file_handler(self):
        """
        创建文件处理器
        
        Returns:
            文件处理器
        """
        log_file = self.config["log_file"]
        
        if self.config["log_rotation"] == "size":
            # 按大小轮转
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.config["max_bytes"],
                backupCount=self.config["backup_count"]
            )
        else:
            # 按时间轮转（每天）
            handler = logging.handlers.TimedRotatingFileHandler(
                log_file,
                when="midnight",
                interval=1,
                backupCount=self.config["backup_count"]
            )
        
        # 设置格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
        )
        handler.setFormatter(formatter)
        
        return handler
    
    def _get_log_level(self, level_name: str) -> int:
        """
        获取日志级别
        
        Args:
            level_name: 级别名称
            
        Returns:
            级别值
        """
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return level_map.get(level_name.upper(), logging.INFO)
    
    def _disable_other_loggers(self):
        """
        禁用其他日志记录器
        """
        # 禁用requests等库的日志
        for logger_name in ["requests", "urllib3", "httpcore"]:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.WARNING)
    
    def debug(self, message: str, *args, **kwargs):
        """
        记录调试日志
        
        Args:
            message: 消息
            *args: 位置参数
            **kwargs: 关键字参数
        """
        if self.logger:
            self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """
        记录信息日志
        
        Args:
            message: 消息
            *args: 位置参数
            **kwargs: 关键字参数
        """
        if self.logger:
            self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """
        记录警告日志
        
        Args:
            message: 消息
            *args: 位置参数
            **kwargs: 关键字参数
        """
        if self.logger:
            self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """
        记录错误日志
        
        Args:
            message: 消息
            *args: 位置参数
            **kwargs: 关键字参数
        """
        if self.logger:
            self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """
        记录严重错误日志
        
        Args:
            message: 消息
            *args: 位置参数
            **kwargs: 关键字参数
        """
        if self.logger:
            self.logger.critical(message, *args, **kwargs)
    
    def log(self, level: int, message: str, *args, **kwargs):
        """
        记录指定级别的日志
        
        Args:
            level: 级别
            message: 消息
            *args: 位置参数
            **kwargs: 关键字参数
        """
        if self.logger:
            self.logger.log(level, message, *args, **kwargs)
    
    def update_config(self, config: Dict):
        """
        更新配置
        
        Args:
            config: 新配置
        """
        with self.lock:
            self.config.update(config)
            
            # 确保目录存在
            os.makedirs(self.config["log_dir"], exist_ok=True)
            os.makedirs(os.path.dirname(self.config["log_file"]), exist_ok=True)
            
            # 重新初始化
            self.initialize()
    
    def get_log_stats(self) -> Dict:
        """
        获取日志统计信息
        
        Returns:
            日志统计信息
        """
        try:
            # 检查日志文件大小
            log_file = self.config["log_file"]
            log_size = os.path.getsize(log_file) if os.path.exists(log_file) else 0
            
            # 检查备份文件数量
            backup_count = 0
            log_dir = os.path.dirname(log_file)
            log_base = os.path.basename(log_file)
            
            for file in os.listdir(log_dir):
                if file.startswith(log_base) and file != log_base:
                    backup_count += 1
            
            return {
                "log_file": log_file,
                "log_size": log_size,
                "backup_count": backup_count,
                "log_level": self.config["log_level"],
                "log_rotation": self.config["log_rotation"],
            }
        except Exception as e:
            return {
                "error": str(e),
                "log_file": self.config["log_file"],
                "log_level": self.config["log_level"],
            }
    
    def get_logger(self) -> logging.Logger:
        """
        获取日志记录器
        
        Returns:
            日志记录器
        """
        return self.logger
    
    def shutdown(self):
        """
        关闭日志管理器
        """
        with self.lock:
            if self.logger:
                # 关闭所有处理器
                for handler in self.logger.handlers:
                    handler.close()
                self.logger.handlers = []
            self.logger = None
    
    def __del__(self):
        """
        析构函数
        """
        self.shutdown()
