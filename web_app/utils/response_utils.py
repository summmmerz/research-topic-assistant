#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
响应工具模块

提供统一的响应处理和错误处理功能
"""

from flask import jsonify
from typing import Dict, Any, Optional, List, Type, Callable


def success_response(data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    生成成功响应
    
    Args:
        data: 响应数据
    
    Returns:
        成功响应字典
    """
    response = {'success': True}
    if data:
        response.update(data)
    return response


def error_response(error: str, status_code: int = 400) -> tuple:
    """
    生成错误响应
    
    Args:
        error: 错误信息
        status_code: HTTP状态码
    
    Returns:
        错误响应元组 (响应字典, 状态码)
    """
    return jsonify({'success': False, 'error': error}), status_code


def component_not_initialized_error(component_name: str) -> tuple:
    """
    生成组件未初始化错误响应
    
    Args:
        component_name: 组件名称
    
    Returns:
        错误响应元组
    """
    return error_response(f'{component_name} not initialized', 500)


def validate_required_params(data: Dict[str, Any], required_params: List[str]) -> Optional[tuple]:
    """
    验证必填参数
    
    Args:
        data: 请求数据
        required_params: 必填参数列表
    
    Returns:
        错误响应元组，如果验证通过则返回None
    """
    for param in required_params:
        if param not in data or not data[param]:
            return error_response(f'{param} is required')
    return None


def handle_exception(exception: Exception, default_message: str = 'Internal server error') -> tuple:
    """
    处理异常
    
    Args:
        exception: 异常对象
        default_message: 默认错误消息
    
    Returns:
        错误响应元组
    """
    print(f"Error: {str(exception)}")
    return error_response(default_message, 500)


def convert_to_enum_list(values: List[str], enum_class: Type) -> List[Any]:
    """
    将字符串列表转换为枚举列表
    
    Args:
        values: 字符串列表
        enum_class: 枚举类
    
    Returns:
        枚举对象列表
    """
    if not values:
        return None
    return [enum_class(v) for v in values]
