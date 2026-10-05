#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公共工具模块

提供通用的工具函数和方法
"""

from typing import Dict, List, Any, Optional
import re


def format_response(response: str, max_length: int = 2048) -> str:
    """
    格式化响应，限制长度
    
    Args:
        response: 响应文本
        max_length: 最大长度
        
    Returns:
        格式化后的响应
    """
    if len(response) > max_length:
        return response[:max_length] + "..."
    return response


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    提取关键词
    
    Args:
        text: 文本
        max_keywords: 最大关键词数量
        
    Returns:
        关键词列表
    """
    # 简单的关键词提取
    # 实际项目中可以使用更复杂的NLP方法
    words = re.findall(r'\b\w+\b', text.lower())
    word_count = {}
    for word in words:
        if len(word) > 2:  # 过滤短词
            word_count[word] = word_count.get(word, 0) + 1
    
    # 排序并返回前N个
    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:max_keywords]]


def validate_input(user_input: str) -> bool:
    """
    验证用户输入
    
    Args:
        user_input: 用户输入
        
    Returns:
        是否有效
    """
    if not user_input:
        return False
    if len(user_input) > 1000:
        return False
    return True


def build_message_history(context: List[Dict[str, str]], user_input: str) -> List[Dict[str, str]]:
    """
    构建消息历史
    
    Args:
        context: 上下文
        user_input: 用户输入
        
    Returns:
        消息历史
    """
    messages = []
    if context:
        messages.extend(context)
    else:
        messages.append({"role": "user", "content": user_input})
    return messages


def get_task_type_from_input(user_input: str) -> str:
    """
    从用户输入中获取任务类型
    
    Args:
        user_input: 用户输入
        
    Returns:
        任务类型
    """
    user_input_lower = user_input.lower()
    
    # 检查选题生成意图
    topic_patterns = [
        r"生成.*选题",
        r"推荐.*题目",
        r"科研.*选题",
        r"研究.*方向",
        r"论文.*题目"
    ]
    for pattern in topic_patterns:
        if re.search(pattern, user_input_lower):
            return "topic_generation"
    
    # 检查文档查询意图
    doc_patterns = [
        r"查询.*文件",
        r"查找.*资料",
        r"搜索.*文档",
        r"读取.*文件",
        r"获取.*信息"
    ]
    for pattern in doc_patterns:
        if re.search(pattern, user_input_lower):
            return "document_query"
    
    # 默认日常对话
    return "general_chat"
