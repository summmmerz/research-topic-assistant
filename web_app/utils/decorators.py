#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装饰器模块

提供请求追踪和智能体检查等装饰器
"""

import time
import uuid
from functools import wraps
from flask import request, g, jsonify

from web_app.utils.agent_manager import get_or_create_agent
from web_app.utils.session_manager import update_request_stats

def track_request(f):
    """追踪请求性能和统计"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 生成请求ID
        request_id = str(uuid.uuid4())[:8]
        g.request_id = request_id
        g.start_time = time.time()
        
        # 记录请求开始
        endpoint = request.endpoint or request.path
        print(f"{request.method} {endpoint}")
        
        try:
            # 执行请求
            response = f(*args, **kwargs)
            
            # 计算响应时间
            elapsed = time.time() - g.start_time
            
            # 更新统计
            update_request_stats(endpoint, elapsed)
            
            # 记录请求完成
            status_code = response[1] if isinstance(response, tuple) else 200
            print(f"完成: {status_code} ({elapsed:.3f}s)")
            
            return response
            
        except Exception as e:
            elapsed = time.time() - g.start_time
            print(f"错误: {str(e)} ({elapsed:.3f}s)")
            raise
    
    return decorated_function

def require_agent(f):
    """装饰器：确保智能体已初始化"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_agent = get_or_create_agent()
        if not current_agent:
            return jsonify({
                'success': False,
                'error': '智能体未初始化，请检查配置',
                'status': 'not_ready'
            }), 503
        return f(*args, **kwargs)
    return decorated_function
