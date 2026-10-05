#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具调用决策模块

负责分析用户输入和上下文，决定是否需要调用工具，以及调用哪些工具
"""

from typing import Dict, List, Any, Optional, Tuple
import json
import re

from app.utils.logger import LogManager
from app.utils.error import ErrorHandler
from app.modules.tool.tool_manager import ToolManager


class ToolDecider:
    """
    工具调用决策器
    """
    
    def __init__(self, tool_manager: ToolManager, logger: LogManager = None, error_handler: ErrorHandler = None):
        """
        初始化工具调用决策器
        
        Args:
            tool_manager: 工具管理器
            logger: 日志管理器
            error_handler: 错误处理器
        """
        self.tool_manager = tool_manager
        self.logger = logger
        self.error_handler = error_handler
        
        # 工具调用模式
        self.tool_patterns = {
            'knowledge_graph_query': [
                r'知识图谱',
                r'图谱.*查询',
                r'查询.*关系',
                r'关联.*(实体|关键词|导师|论文|方向)',
                r'.*导师.*研究.*方向'
            ],
            'api_request': [
                r'获取.*数据',
                r'查询.*API',
                r'调用.*接口',
                r'请求.*数据'
            ],
            'database_query': [
                r'查询.*数据库',
                r'统计.*数据',
                r'分析.*数据',
                r'获取.*记录'
            ],
            'local_command': [
                r'执行.*命令',
                r'运行.*程序',
                r'启动.*服务',
                r'检查.*状态'
            ]
        }
        
        # 工具参数提取模式
        self.param_patterns = {
            'knowledge_graph_query': {
                'question': r'(.+)'
            },
            'api_request': {
                'url': r'URL[:：]\s*(\S+)',
                'method': r'(GET|POST|PUT|DELETE)',
                'params': r'参数[:：]\s*({[^}]+})'
            },
            'database_query': {
                'query': r'SQL[:：]\s*(.+?)(?=\s*参数|$)',
                'args': r'参数[:：]\s*\[(.*?)\]'
            },
            'local_command': {
                'command': r'命令[:：]\s*(.+?)(?=\s*超时|$)',
                'timeout': r'超时[:：]\s*(\d+)'
            }
        }
    
    def analyze_user_input(self, user_input: str, context: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        分析用户输入，决定是否需要调用工具
        
        Args:
            user_input: 用户输入
            context: 上下文
            
        Returns:
            分析结果
        """
        try:
            if self.logger:
                self.logger.info(f"分析用户输入: {user_input}")
            
            # 检查是否需要调用工具
            tool_call_info = self._detect_tool_need(user_input)
            
            if not tool_call_info:
                return {
                    'need_tool': False,
                    'reason': '用户输入不包含工具调用需求'
                }
            
            # 提取工具参数
            tool_params = self._extract_tool_params(tool_call_info['tool_type'], user_input)
            
            # 选择合适的工具
            tool_name = self._select_tool(tool_call_info['tool_type'], tool_params)
            
            if not tool_name:
                return {
                    'need_tool': False,
                    'reason': f'没有找到适合的{tool_call_info["tool_type"]}类型工具'
                }
            
            return {
                'need_tool': True,
                'tool_type': tool_call_info['tool_type'],
                'tool_name': tool_name,
                'params': tool_params,
                'reason': f'检测到{tool_call_info["tool_type"]}工具调用需求'
            }
            
        except Exception as e:
            error_msg = str(e)
            if self.logger:
                self.logger.error(f"分析用户输入错误: {error_msg}")
            if self.error_handler:
                self.error_handler.handle_error(e, "分析用户输入错误")
            return {
                'need_tool': False,
                'reason': f'分析用户输入时发生错误: {error_msg}'
            }
    
    def _detect_tool_need(self, user_input: str) -> Optional[Dict[str, str]]:
        """
        检测用户输入是否需要调用工具
        
        Args:
            user_input: 用户输入
            
        Returns:
            工具调用信息
        """
        for tool_type, patterns in self.tool_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return {
                        'tool_type': tool_type
                    }
        return None
    
    def _extract_tool_params(self, tool_type: str, user_input: str) -> Dict[str, Any]:
        """
        提取工具参数
        
        Args:
            tool_type: 工具类型
            user_input: 用户输入
            
        Returns:
            工具参数
        """
        params = {}
        
        if tool_type in self.param_patterns:
            patterns = self.param_patterns[tool_type]
            for param_name, pattern in patterns.items():
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    # 处理JSON格式的参数
                    if param_name == 'params':
                        try:
                            value = json.loads(value)
                        except json.JSONDecodeError:
                            pass
                    # 处理数字类型参数
                    elif param_name == 'timeout':
                        try:
                            value = int(value)
                        except ValueError:
                            pass
                    params[param_name] = value
        
        return params
    
    def _select_tool(self, tool_type: str, params: Dict[str, Any]) -> Optional[str]:
        """
        选择合适的工具
        
        Args:
            tool_type: 工具类型
            params: 工具参数
            
        Returns:
            工具名称
        """
        all_tools = self.tool_manager.get_all_tools()
        if tool_type == 'knowledge_graph_query' and 'knowledge_graph_query' in all_tools:
            return 'knowledge_graph_query'
        
        # 根据工具类型和参数选择合适的工具
        for tool_name, tool in all_tools.items():
            # 这里可以根据工具类型和参数进行更复杂的匹配逻辑
            # 暂时简单返回第一个匹配的工具
            return tool_name
        
        return None
    
    def handle_tool_result(self, tool_result: Dict[str, Any], user_input: str) -> str:
        """
        处理工具执行结果，生成响应
        
        Args:
            tool_result: 工具执行结果
            user_input: 用户输入
            
        Returns:
            响应文本
        """
        try:
            if tool_result.get('success'):
                data = tool_result.get('data', {})
                # 生成成功响应
                if isinstance(data, dict):
                    # 处理字典类型结果
                    response = f"工具执行成功，结果如下：\n"
                    for key, value in data.items():
                        response += f"- {key}: {value}\n"
                elif isinstance(data, list):
                    # 处理列表类型结果
                    response = f"工具执行成功，返回了{len(data)}条结果：\n"
                    for i, item in enumerate(data[:10]):  # 只显示前10条
                        response += f"{i+1}. {item}\n"
                    if len(data) > 10:
                        response += f"... 还有{len(data) - 10}条结果未显示\n"
                else:
                    # 处理其他类型结果
                    response = f"工具执行成功，结果：{data}\n"
            else:
                # 生成失败响应
                error_message = tool_result.get('error', '未知错误')
                response = f"工具执行失败：{error_message}\n"
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            if self.logger:
                self.logger.error(f"处理工具结果错误: {error_msg}")
            if self.error_handler:
                self.error_handler.handle_error(e, "处理工具结果错误")
            return f"处理工具结果时发生错误：{error_msg}\n"
    
    def get_tool_suggestions(self, user_input: str) -> List[Dict[str, Any]]:
        """
        获取工具使用建议
        
        Args:
            user_input: 用户输入
            
        Returns:
            工具建议列表
        """
        suggestions = []
        all_tools = self.tool_manager.get_all_tool_info()
        
        # 根据用户输入推荐工具
        for tool_info in all_tools:
            # 简单匹配工具描述和用户输入
            if any(keyword in user_input for keyword in tool_info['description']):
                suggestions.append({
                    'tool_name': tool_info['name'],
                    'description': tool_info['description'],
                    'reason': f'工具描述包含用户输入的关键词'
                })
        
        return suggestions
