#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具管理器模块

负责工具的注册、管理和调用
"""

from typing import Dict, List, Any, Optional, Callable, Union
import time
import threading
import traceback
from abc import ABC, abstractmethod

from app.utils.logger import LogManager
from app.utils.error import ErrorHandler


class ToolBase(ABC):
    """
    工具基类
    """
    
    def __init__(self, name: str, description: str, **kwargs):
        """
        初始化工具
        
        Args:
            name: 工具名称
            description: 工具描述
        """
        self.name = name
        self.description = description
        self.kwargs = kwargs
        self.logger = kwargs.get('logger')
        
    @abstractmethod
    def execute(self, **params) -> Dict[str, Any]:
        """
        执行工具
        
        Args:
            **params: 工具参数
            
        Returns:
            执行结果
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取工具信息
        
        Returns:
            工具信息
        """
        return {
            'name': self.name,
            'description': self.description
        }


class APIRequestTool(ToolBase):
    """
    API请求工具
    """
    
    def __init__(self, name: str, description: str, api_url: str, method: str = 'GET', **kwargs):
        """
        初始化API请求工具
        
        Args:
            name: 工具名称
            description: 工具描述
            api_url: API URL
            method: 请求方法
        """
        super().__init__(name, description, **kwargs)
        self.api_url = api_url
        self.method = method.upper()
        
    def execute(self, **params) -> Dict[str, Any]:
        """
        执行API请求
        
        Args:
            **params: 请求参数
            
        Returns:
            执行结果
        """
        try:
            import requests
            
            if self.method == 'GET':
                response = requests.get(self.api_url, params=params, timeout=30)
            elif self.method == 'POST':
                response = requests.post(self.api_url, json=params, timeout=30)
            else:
                return {
                    'success': False,
                    'error': f"不支持的请求方法: {self.method}"
                }
            
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class DatabaseQueryTool(ToolBase):
    """
    数据库查询工具
    """
    
    def __init__(self, name: str, description: str, db_connector: Callable, **kwargs):
        """
        初始化数据库查询工具
        
        Args:
            name: 工具名称
            description: 工具描述
            db_connector: 数据库连接函数
        """
        super().__init__(name, description, **kwargs)
        self.db_connector = db_connector
        
    def execute(self, **params) -> Dict[str, Any]:
        """
        执行数据库查询
        
        Args:
            **params: 查询参数
            
        Returns:
            执行结果
        """
        try:
            query = params.get('query')
            if not query:
                return {
                    'success': False,
                    'error': '查询语句不能为空'
                }
            
            # 执行查询
            result = self.db_connector(query, params.get('args', []))
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class LocalCommandTool(ToolBase):
    """
    本地命令执行工具
    """
    
    def __init__(self, name: str, description: str, **kwargs):
        """
        初始化本地命令执行工具
        
        Args:
            name: 工具名称
            description: 工具描述
        """
        super().__init__(name, description, **kwargs)
        
    def execute(self, **params) -> Dict[str, Any]:
        """
        执行本地命令
        
        Args:
            **params: 命令参数
            
        Returns:
            执行结果
        """
        try:
            import subprocess
            
            command = params.get('command')
            if not command:
                return {
                    'success': False,
                    'error': '命令不能为空'
                }
            
            # 执行命令
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=params.get('timeout', 30)
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class ToolManager:
    """
    工具管理器
    """
    
    def __init__(self, config: Dict[str, Any] = None, logger: LogManager = None, error_handler: ErrorHandler = None):
        """
        初始化工具管理器
        
        Args:
            config: 配置信息
            logger: 日志管理器
            error_handler: 错误处理器
        """
        self.config = config or {}
        self.logger = logger
        self.error_handler = error_handler
        self.tools: Dict[str, ToolBase] = {}
        self.permissions: Dict[str, List[str]] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.lock = threading.RLock()
        
    def register_tool(self, tool: ToolBase, permissions: List[str] = None):
        """
        注册工具
        
        Args:
            tool: 工具实例
            permissions: 权限列表
        """
        with self.lock:
            self.tools[tool.name] = tool
            if permissions:
                self.permissions[tool.name] = permissions
            if self.logger:
                self.logger.info(f"工具注册成功: {tool.name}")
    
    def unregister_tool(self, tool_name: str):
        """
        注销工具
        
        Args:
            tool_name: 工具名称
        """
        with self.lock:
            if tool_name in self.tools:
                del self.tools[tool_name]
                if tool_name in self.permissions:
                    del self.permissions[tool_name]
                if self.logger:
                    self.logger.info(f"工具注销成功: {tool_name}")
    
    def get_tool(self, tool_name: str) -> Optional[ToolBase]:
        """
        获取工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具实例
        """
        with self.lock:
            return self.tools.get(tool_name)
    
    def get_all_tools(self) -> Dict[str, ToolBase]:
        """
        获取所有工具
        
        Returns:
            工具字典
        """
        with self.lock:
            return self.tools.copy()
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具信息
        """
        tool = self.get_tool(tool_name)
        if tool:
            return tool.get_info()
        return None
    
    def get_all_tool_info(self) -> List[Dict[str, Any]]:
        """
        获取所有工具信息
        
        Returns:
            工具信息列表
        """
        return [tool.get_info() for tool in self.tools.values()]
    
    def has_permission(self, tool_name: str, user_role: str) -> bool:
        """
        检查权限
        
        Args:
            tool_name: 工具名称
            user_role: 用户角色
            
        Returns:
            是否有权限
        """
        with self.lock:
            # 如果没有设置权限，则默认允许
            if tool_name not in self.permissions:
                return True
            # 检查用户角色是否在权限列表中
            return user_role in self.permissions[tool_name]
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any], user_role: str = 'default', timeout: int = 30) -> Dict[str, Any]:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            user_role: 用户角色
            timeout: 超时时间（秒）
            
        Returns:
            执行结果
        """
        start_time = time.time()
        execution_id = f"{tool_name}_{int(start_time * 1000)}"
        
        # 记录执行开始
        execution_record = {
            'id': execution_id,
            'tool_name': tool_name,
            'params': params,
            'user_role': user_role,
            'start_time': start_time,
            'end_time': None,
            'result': None
        }
        
        try:
            # 检查工具是否存在
            tool = self.get_tool(tool_name)
            if not tool:
                result = {
                    'success': False,
                    'error': f"工具不存在: {tool_name}"
                }
                if self.logger:
                    self.logger.error(f"工具不存在: {tool_name}")
                return result
            
            # 检查权限
            if not self.has_permission(tool_name, user_role):
                result = {
                    'success': False,
                    'error': f"无权限执行工具: {tool_name}"
                }
                if self.logger:
                    self.logger.warning(f"用户 {user_role} 无权限执行工具: {tool_name}")
                return result
            
            if self.logger:
                self.logger.info(f"执行工具: {tool_name}, 参数: {params}")
            
            # 执行工具（带超时处理）
            def execute_with_timeout():
                return tool.execute(**params)
            
            thread = threading.Thread(target=execute_with_timeout)
            thread.daemon = True
            thread.start()
            thread.join(timeout)
            
            if thread.is_alive():
                result = {
                    'success': False,
                    'error': f"工具执行超时: {timeout}秒"
                }
                if self.logger:
                    self.logger.error(f"工具执行超时: {tool_name}")
            else:
                # 这里需要修改，因为线程无法直接返回结果
                # 改用直接执行的方式，后续可以考虑使用更复杂的线程通信
                result = tool.execute(**params)
            
            if self.logger:
                self.logger.info(f"工具执行完成: {tool_name}, 结果: {result}")
                
        except Exception as e:
            error_msg = str(e)
            result = {
                'success': False,
                'error': error_msg
            }
            if self.logger:
                self.logger.error(f"工具执行错误: {tool_name}, 错误: {error_msg}")
            if self.error_handler:
                self.error_handler.handle_error(e, f"工具执行错误: {tool_name}")
        finally:
            # 记录执行结束
            end_time = time.time()
            execution_record['end_time'] = end_time
            execution_record['result'] = result
            execution_record['duration'] = end_time - start_time
            
            with self.lock:
                self.execution_history.append(execution_record)
                # 限制历史记录长度
                if len(self.execution_history) > 1000:
                    self.execution_history = self.execution_history[-1000:]
        
        return result
    
    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取执行历史
        
        Args:
            limit: 限制数量
            
        Returns:
            执行历史
        """
        with self.lock:
            return self.execution_history[-limit:]
    
    def clear_execution_history(self):
        """
        清空执行历史
        """
        with self.lock:
            self.execution_history.clear()
            if self.logger:
                self.logger.info("执行历史已清空")
    
    def shutdown(self):
        """
        关闭工具管理器
        """
        if self.logger:
            self.logger.info("关闭工具管理器")
        # 可以在这里添加清理逻辑
