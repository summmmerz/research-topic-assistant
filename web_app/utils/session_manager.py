#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话管理器模块

负责管理用户会话和会话清理
"""

import threading
from datetime import datetime, timedelta
from typing import Dict, Any

from .redis_session_store import RedisWebSessionStore

# 用户会话管理
user_sessions: Dict[str, Dict[str, Any]] = {}
redis_session_store = None
session_storage = "memory"
session_lock = threading.Lock()
request_stats_lock = threading.Lock()

# 请求统计
request_stats = {
    'total_requests': 0,
    'total_messages': 0,
    'total_response_time': 0,
    'active_sessions': 0,
    'start_time': datetime.now(),
    'endpoints': {}
}

def configure_session_store(config: Dict[str, Any]):
    """Enable Redis-backed web sessions when available."""
    global redis_session_store, session_storage
    redis_config = (config or {}).get("redis") or config or {}
    redis_session_store = RedisWebSessionStore(redis_config)
    session_storage = "redis" if redis_session_store.available else "memory"

def get_user_session(session_id: str) -> Dict[str, Any]:
    """
    获取或创建用户会话
    
    Args:
        session_id: 会话ID
    
    Returns:
        会话数据字典
    """
    with session_lock:
        now = datetime.now().isoformat()
        if session_id not in user_sessions and session_storage == "redis" and redis_session_store:
            cached_session = redis_session_store.get(session_id)
            if cached_session:
                user_sessions[session_id] = cached_session

        if session_id not in user_sessions:
            user_sessions[session_id] = {
                'user_id': f'web_user_{session_id[:8]}',
                'session_id': session_id,
                'created_at': now,
                'last_activity': now,
                'chat_history': [],
                'settings': {
                    'stream_output': True,
                    'chunk_size': 10,
                    'delay': 0.05,
                    'theme': 'light',
                    'layout': 'default',
                    'font_size': 14,
                    'auto_scroll': True,
                    'sound_effects': False,
                    'desktop_notifications': False,
                    'auto_save': True
                },
                'stats': {
                    'message_count': 0,
                    'total_response_time': 0
                }
            }
            request_stats['active_sessions'] = len(user_sessions)
        else:
            # 更新最后活动时间
            user_sessions[session_id]['last_activity'] = now
        if session_storage == "redis" and redis_session_store:
            try:
                redis_session_store.set(session_id, user_sessions[session_id])
            except Exception:
                pass
        
        return user_sessions[session_id]

def cleanup_old_sessions(max_age_hours: int = 24):
    """
    清理过期的会话
    
    Args:
        max_age_hours: 最大会话存活时间（小时）
    """
    with session_lock:
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session_data in user_sessions.items():
            last_activity = datetime.fromisoformat(session_data['last_activity'])
            if current_time - last_activity > timedelta(hours=max_age_hours):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del user_sessions[session_id]
            if session_storage == "redis" and redis_session_store:
                redis_session_store.delete(session_id)
            print(f"已清理过期会话: {session_id}")
        
        request_stats['active_sessions'] = len(user_sessions)

def get_request_stats() -> Dict[str, Any]:
    """
    获取请求统计信息
    
    Returns:
        请求统计数据
    """
    with request_stats_lock:
        return {
            **request_stats,
            'session_storage': session_storage,
            'redis_sessions': redis_session_store.status() if redis_session_store else None,
            'endpoints': {
                endpoint: stats.copy()
                for endpoint, stats in request_stats['endpoints'].items()
            }
        }

def update_request_stats(endpoint: str, response_time: float):
    """
    更新请求统计信息
    
    Args:
        endpoint: 请求端点
        response_time: 响应时间
    """
    with request_stats_lock:
        request_stats['total_requests'] += 1
        request_stats['total_response_time'] += response_time
        
        if endpoint not in request_stats['endpoints']:
            request_stats['endpoints'][endpoint] = {
                'count': 0,
                'total_time': 0,
                'avg_time': 0
            }
        
        request_stats['endpoints'][endpoint]['count'] += 1
        request_stats['endpoints'][endpoint]['total_time'] += response_time
        request_stats['endpoints'][endpoint]['avg_time'] = (
            request_stats['endpoints'][endpoint]['total_time'] / 
            request_stats['endpoints'][endpoint]['count']
        )

def increment_message_count():
    """
    增加消息计数
    """
    with request_stats_lock:
        request_stats['total_messages'] += 1
