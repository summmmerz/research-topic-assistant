#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理器模块

负责处理系统中的错误和异常情况
"""

from typing import Dict, List, Any, Optional
import traceback
import time
import threading
import json
import os


class ErrorHandler:
    """
    错误处理器类
    """
    
    def __init__(self, config: Dict[str, Any], logger: Any):
        """
        初始化错误处理器
        
        Args:
            config: 配置参数
            logger: 日志记录器
        """
        # 配置
        self.config = {
            "error_log_file": config.get("error_log_file", "data/error_log.json"),  # 错误日志文件
            "max_error_logs": config.get("max_error_logs", 1000),  # 最大错误日志数
            "error_threshold": config.get("error_threshold", 10),  # 错误阈值
            "error_window": config.get("error_window", 60),  # 错误窗口（秒）
            "retry_delay": config.get("retry_delay", 1),  # 重试延迟（秒）
            "max_retries": config.get("max_retries", 3),  # 最大重试次数
        }
        
        # 日志记录器
        self.logger = logger
        
        # 错误计数
        self.error_count = 0
        self.error_times = []
        
        # 错误日志
        self.error_logs = []
        
        # 线程锁
        self.lock = threading.RLock()
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.config["error_log_file"]), exist_ok=True)
    
    def handle_error(self, error: Exception, message: str = "未知错误") -> Dict[str, Any]:
        """
        处理错误
        
        Args:
            error: 错误对象
            message: 错误消息
            
        Returns:
            错误信息字典
        """
        with self.lock:
            # 构建错误信息
            error_info = {
                "timestamp": time.time(),
                "message": message,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc(),
            }
            
            # 记录错误
            self._log_error(error_info)
            
            # 更新错误计数
            self._update_error_count()
            
            # 检查错误率
            if self._check_error_rate():
                self.logger.warning("错误率过高，可能需要系统维护")
            
            return error_info
    
    def _log_error(self, error_info: Dict[str, Any]):
        """
        记录错误
        
        Args:
            error_info: 错误信息
        """
        # 添加到内存日志
        self.error_logs.append(error_info)
        
        # 限制错误日志数量
        if len(self.error_logs) > self.config["max_error_logs"]:
            self.error_logs = self.error_logs[-self.config["max_error_logs"]:]
        
        # 保存到文件
        self._save_error_logs()
        
        # 记录到日志
        self.logger.error(f"{error_info['message']}: {error_info['error_type']}: {error_info['error_message']}")
        self.logger.debug(f"错误堆栈: {error_info['traceback']}")
    
    def _save_error_logs(self):
        """
        保存错误日志到文件
        """
        try:
            with open(self.config["error_log_file"], "w", encoding="utf-8") as f:
                json.dump(self.error_logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存错误日志失败: {str(e)}")
    
    def _update_error_count(self):
        """
        更新错误计数
        """
        current_time = time.time()
        
        # 添加当前错误时间
        self.error_times.append(current_time)
        
        # 移除窗口外的错误时间
        self.error_times = [t for t in self.error_times if current_time - t < self.config["error_window"]]
        
        # 更新错误计数
        self.error_count = len(self.error_times)
    
    def _check_error_rate(self) -> bool:
        """
        检查错误率
        
        Returns:
            是否超过错误阈值
        """
        return self.error_count > self.config["error_threshold"]
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        获取错误统计信息
        
        Returns:
            错误统计信息
        """
        with self.lock:
            # 计算最近错误率
            recent_errors = [e for e in self.error_logs if time.time() - e["timestamp"] < 3600]  # 最近1小时
            
            # 按错误类型分组
            error_types = {}
            for error in self.error_logs:
                error_type = error["error_type"]
                if error_type not in error_types:
                    error_types[error_type] = 0
                error_types[error_type] += 1
            
            return {
                "total_errors": len(self.error_logs),
                "recent_errors": len(recent_errors),
                "error_count": self.error_count,
                "error_types": error_types,
                "error_threshold": self.config["error_threshold"],
            }
    
    def get_recent_errors(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的错误
        
        Args:
            count: 错误数量
            
        Returns:
            最近的错误列表
        """
        with self.lock:
            return self.error_logs[-count:]
    
    def clear_error_logs(self):
        """
        清除错误日志
        """
        with self.lock:
            self.error_logs = []
            self.error_count = 0
            self.error_times = []
            self._save_error_logs()
            self.logger.info("错误日志已清除")
    
    def load_error_logs(self):
        """
        加载错误日志
        """
        try:
            with self.lock:
                if os.path.exists(self.config["error_log_file"]):
                    with open(self.config["error_log_file"], "r", encoding="utf-8") as f:
                        self.error_logs = json.load(f)
                    
                    # 更新错误计数
                    current_time = time.time()
                    self.error_times = [
                        e["timestamp"] for e in self.error_logs 
                        if current_time - e["timestamp"] < self.config["error_window"]
                    ]
                    self.error_count = len(self.error_times)
                    
                    self.logger.info(f"错误日志加载完成，共 {len(self.error_logs)} 条错误")
                else:
                    self.logger.info("错误日志文件不存在")
        except Exception as e:
            self.logger.error(f"加载错误日志失败: {str(e)}")
    
    def update_config(self, config: Dict[str, Any]):
        """
        更新配置
        
        Args:
            config: 新配置
        """
        with self.lock:
            self.config.update(config)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config["error_log_file"]), exist_ok=True)
            
            # 限制错误日志数量
            if len(self.error_logs) > self.config["max_error_logs"]:
                self.error_logs = self.error_logs[-self.config["max_error_logs"]:]
                self._save_error_logs()
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取状态
        
        Returns:
            状态信息
        """
        return {
            "error_count": self.error_count,
            "error_logs_count": len(self.error_logs),
            "error_threshold": self.config["error_threshold"],
            "error_window": self.config["error_window"],
        }
    
    def shutdown(self):
        """
        关闭错误处理器
        """
        # 保存错误日志
        self._save_error_logs()
        self.logger.info("错误处理器关闭")
