#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能科研选题助手 - Web应用主入口

提供智能科研选题助手的Web服务
支持实时聊天、流式输出、主题设置等功能
"""

# 启动信息已移至主程序入口

import os
import sys
import json
import time
import threading
import uuid
import importlib.util
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, g, send_from_directory, redirect
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 导入工具模块
from web_app.utils import (
    get_user_session,
    cleanup_old_sessions,
    get_request_stats,
    increment_message_count,
    get_or_create_agent,
    get_agent_init_status,
    get_agent,
    track_request,
    require_agent,
    error_response,
    configure_session_store
)

# 创建Flask应用
app = Flask(__name__, 
    template_folder='templates',
    static_folder='static'
)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# 启用CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 创建SocketIO实例
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=10 * 1024 * 1024  # 10MB
)

try:
    config_path = os.path.join(project_root, "config", "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as file:
            app_runtime_config = json.load(file)
        configure_session_store(app_runtime_config.get("redis", {}))
except Exception:
    pass

# 导入日志和错误处理模块

from app.utils.logger import LogManager
from app.utils.error import ErrorHandler

# 初始化日志管理器
log_manager = LogManager({
    'log_dir': os.path.join(project_root, 'data', 'logs'),
    'log_file': os.path.join(project_root, 'data', 'logs', 'web_app.log'),
    'log_level': 'INFO',
    'log_rotation': 'daily',
    'backup_count': 7
})
log_manager.initialize()

# 初始化错误处理器
error_handler = ErrorHandler({
    'error_log_file': os.path.join(project_root, 'data', 'error_log.json'),
    'max_error_logs': 1000,
    'error_threshold': 10,
    'error_window': 60
}, log_manager)
error_handler.load_error_logs()

# ==================== 路由定义 ====================

def _vue_build_dir() -> str:
    return os.path.join(app.static_folder, 'vue')


def _vue_build_available() -> bool:
    return os.path.exists(os.path.join(_vue_build_dir(), 'index.html'))


@app.route('/')
def index():
    """首页 - 渲染主界面"""
    return redirect('/vue/')


@app.route('/test-js')
def test_js():
    """Legacy test page removed from the thesis deployment surface."""
    return redirect('/vue/')


@app.route('/topic-recommendation')
def topic_recommendation():
    """Legacy Flask page path kept as a compatibility redirect."""
    return redirect('/vue/topic-recommendation')


@app.route('/knowledge-graph')
def knowledge_graph():
    """Legacy Flask page path kept as a compatibility redirect."""
    return redirect('/vue/knowledge-graph')


@app.route('/vue/')
@app.route('/vue/<path:path>')
def vue_app(path: str = 'index.html'):
    """Serve the Vue 3 + Element Plus + ECharts frontend."""
    vue_dir = _vue_build_dir()
    requested = os.path.join(vue_dir, path)
    if path != 'index.html' and os.path.exists(requested):
        return send_from_directory(vue_dir, path)
    return send_from_directory(vue_dir, 'index.html')





@app.route('/api/status')
@track_request
def api_status():
    """
    API状态检查
    
    Returns:
        系统状态信息
    """
    current_agent = get_or_create_agent()
    stats = get_request_stats()
    agent_status = get_agent_init_status()
    
    uptime = datetime.now() - stats['start_time']
    uptime_str = f"{uptime.days}天 {uptime.seconds // 3600}小时 {(uptime.seconds // 60) % 60}分钟"
    
    if current_agent and current_agent.is_initialized:
        status = current_agent.get_status()
        return jsonify({
            'success': True,
            'status': 'ready',
            'agent_initialized': True,
            'models': status.get('models', {}),
            'document_retrieval': status.get('document_retrieval', {}),
            'uptime': uptime_str,
            'stats': {
                'total_requests': stats['total_requests'],
                'total_messages': stats['total_messages'],
                'active_sessions': stats['active_sessions']
            },
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({
            'success': True,
            'status': 'initializing',
            'agent_initialized': False,
            'message': '智能体正在初始化中...',
            'error': agent_status.get('error'),
            'uptime': uptime_str,
            'timestamp': datetime.now().isoformat()
        })


@app.route('/api/chat', methods=['POST'])
@track_request
@require_agent
def api_chat():
    """
    聊天API - 非流式输出
    
    Request Body:
        - message: 用户输入消息
        - session_id: 会话ID
        - function: 功能类型（可选）
    
    Returns:
        助手响应
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response('请求体不能为空')
        
        user_input = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        function_type = data.get('function', 'general_chat')
        
        # 验证输入
        if not user_input:
            return error_response('消息不能为空')
        
        if len(user_input) > 2000:
            return error_response('消息长度超过限制（最大2000字符）')
        
        # 获取用户会话
        user_session = get_user_session(session_id)
        user_id = user_session['user_id']
        
        # 获取智能体
        current_agent = get_or_create_agent()
        
        # 添加到历史记录
        user_session['chat_history'].append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().isoformat(),
            'function': function_type
        })
        
        # 处理请求
        start_time = time.time()
        
        response = current_agent.process_user_input(user_input, user_id)
        response_time = time.time() - start_time
        
        response_text = response.get('response', '')
        
        # 添加到历史记录
        user_session['chat_history'].append({
            'role': 'assistant',
            'content': response_text,
            'timestamp': datetime.now().isoformat(),
            'response_time': response_time
        })
        
        # 更新统计
        user_session['stats']['message_count'] += 1
        user_session['stats']['total_response_time'] += response_time
        increment_message_count()
        stats = get_request_stats()
        stats['total_response_time'] += response_time
        
        return jsonify({
            'success': True,
            'streaming': False,
            'response': response_text,
            'response_time': round(response_time, 3),
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        # 仅在调试模式下打印详细错误信息
        # print(f"处理聊天请求时发生错误: {str(e)}")
        return error_response('处理请求时发生错误', 500)


@app.route('/api/chat/stream', methods=['POST'])
@track_request
@require_agent
def api_chat_stream():
    """
    聊天API - 流式输出（Server-Sent Events）
    
    Request Body:
        - message: 用户输入消息
        - session_id: 会话ID
        - settings: 流式设置（可选）
    
    Returns:
        SSE流
    """
    def generate():
        try:
            data = request.get_json()
            user_input = data.get('message', '').strip()
            session_id = data.get('session_id', 'default')
            settings = data.get('settings', {})
            
            if not user_input:
                yield f"data: {json.dumps({'error': '消息不能为空'})}\n\n"
                return
            
            # 获取用户会话
            user_session = get_user_session(session_id)
            user_id = user_session['user_id']
            
            # 获取智能体
            current_agent = get_or_create_agent()
            
            # 添加到历史记录
            user_session['chat_history'].append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now().isoformat()
            })
            
            # 流式处理
            start_time = time.time()
            full_response = ""
            
            chunk_size = settings.get('chunk_size', 10)
            delay = settings.get('delay', 0.05)
            
            yield f"data: {json.dumps({'event': 'start'})}\n\n"
            
            for chunk in current_agent.stream_process_user_input(
                user_input,
                user_id,
                stream_chunk_size=chunk_size,
                stream_delay=delay
            ):
                full_response += chunk
                yield f"data: {json.dumps({'event': 'chunk', 'data': chunk})}\n\n"
            
            response_time = time.time() - start_time
            
            # 添加到历史记录
            user_session['chat_history'].append({
                'role': 'assistant',
                'content': full_response,
                'timestamp': datetime.now().isoformat(),
                'response_time': response_time
            })
            
            # 更新统计
            user_session['stats']['message_count'] += 1
            user_session['stats']['total_response_time'] += response_time
            increment_message_count()
            
            yield f"data: {json.dumps({'event': 'end', 'response_time': round(response_time, 3)})}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
    
    return app.response_class(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@app.route('/api/history', methods=['GET'])
@track_request
def api_history():
    """
    获取聊天历史
    
    Query Parameters:
        - session_id: 会话ID
        - limit: 返回记录数量限制（可选，默认100）
    
    Returns:
        聊天历史记录
    """
    session_id = request.args.get('session_id', 'default')
    limit = request.args.get('limit', 100, type=int)
    
    user_session = get_user_session(session_id)
    history = user_session['chat_history'][-limit:] if limit > 0 else user_session['chat_history']
    
    return jsonify({
        'success': True,
        'history': history,
        'total': len(user_session['chat_history']),
        'session_id': session_id,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/history/clear', methods=['POST'])
@track_request
def api_clear_history():
    """
    清空聊天历史
    
    Request Body:
        - session_id: 会话ID
    
    Returns:
        操作结果
    """
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id', 'default')
        
        user_session = get_user_session(session_id)
        user_session['chat_history'] = []
        
        return jsonify({
            'success': True,
            'message': '历史记录已清空',
            'session_id': session_id
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'清空历史记录失败: {str(e)}'
        }), 500


@app.route('/api/history/export', methods=['GET'])
@track_request
def api_export_history():
    """
    导出聊天历史
    
    Query Parameters:
        - session_id: 会话ID
        - format: 导出格式（txt, json，默认txt）
    
    Returns:
        导出的文件
    """
    session_id = request.args.get('session_id', 'default')
    export_format = request.args.get('format', 'txt')
    
    user_session = get_user_session(session_id)
    history = user_session['chat_history']
    
    if export_format == 'json':
        # JSON格式
        export_data = {
            'session_id': session_id,
            'exported_at': datetime.now().isoformat(),
            'history': history
        }
        
        filename = f"chat_history_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return jsonify({
            'success': True,
            'data': export_data,
            'filename': filename
        })
    
    else:
        # 文本格式
        lines = []
        lines.append(f"智能科研选题助手 - 对话记录")
        lines.append(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"会话ID: {session_id}")
        lines.append("")
        
        for msg in history:
            role = "用户" if msg['role'] == 'user' else "助手"
            time_str = datetime.fromisoformat(msg['timestamp']).strftime('%Y-%m-%d %H:%M')
            lines.append(f"[{time_str}] {role}: {msg['content']}")
        
        content = "\n".join(lines)
        filename = f"chat_history_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        return jsonify({
            'success': True,
            'content': content,
            'filename': filename
        })


@app.route('/api/settings', methods=['GET', 'POST'])
@track_request
def api_settings():
    """
    获取或更新设置
    
    GET: 获取当前设置
    POST: 更新设置
    
    Returns:
        设置信息
    """
    session_id = request.args.get('session_id', 'default') if request.method == 'GET' else request.get_json().get('session_id', 'default')
    user_session = get_user_session(session_id)
    
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'settings': user_session['settings'],
            'session_id': session_id
        })
    
    else:  # POST
        try:
            data = request.get_json()
            new_settings = data.get('settings', {})
            
            # 验证设置值
            valid_settings = {
                'stream_output': bool,
                'chunk_size': int,
                'delay': float,
                'theme': str,
                'layout': str,
                'font_size': int,
                'auto_scroll': bool,
                'sound_effects': bool,
                'desktop_notifications': bool,
                'auto_save': bool
            }
            
            # 更新设置
            for key, value in new_settings.items():
                if key in valid_settings:
                    try:
                        user_session['settings'][key] = valid_settings[key](value)
                    except (ValueError, TypeError):
                        pass  # 忽略无效值
            
            return jsonify({
                'success': True,
                'settings': user_session['settings'],
                'session_id': session_id
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'更新设置失败: {str(e)}'
            }), 500


@app.route('/api/settings/reset', methods=['POST'])
@track_request
def api_reset_settings():
    """
    重置设置为默认值
    
    Request Body:
        - session_id: 会话ID
    
    Returns:
        重置后的设置
    """
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id', 'default')
        
        user_session = get_user_session(session_id)
        user_session['settings'] = {
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
        }
        
        return jsonify({
            'success': True,
            'settings': user_session['settings'],
            'message': '设置已重置为默认值',
            'session_id': session_id
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'重置设置失败: {str(e)}'
        }), 500


@app.route('/api/stats', methods=['GET'])
@track_request
def api_stats():
    """
    获取系统统计信息
    
    Returns:
        统计数据
    """
    stats = get_request_stats()
    uptime = datetime.now() - stats['start_time']
    
    avg_response_time = 0
    if stats['total_requests'] > 0:
        avg_response_time = stats['total_response_time'] / stats['total_requests']
    
    return jsonify({
        'success': True,
        'stats': {
            'total_requests': stats['total_requests'],
            'total_messages': stats['total_messages'],
            'active_sessions': stats['active_sessions'],
            'avg_response_time': round(avg_response_time, 3),
            'uptime_seconds': uptime.total_seconds(),
            'uptime_formatted': f"{uptime.days}天 {uptime.seconds // 3600}小时 {(uptime.seconds // 60) % 60}分钟",
            'endpoints': stats['endpoints']
        },
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/session/new', methods=['POST'])
@track_request
def api_new_session():
    """
    创建新会话
    
    Returns:
        新会话信息
    """
    try:
        new_session_id = f"session_{uuid.uuid4().hex[:16]}"
        
        user_session = get_user_session(new_session_id)
        
        return jsonify({
            'success': True,
            'session_id': new_session_id,
            'created_at': user_session['created_at'],
            'message': '新会话已创建'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'创建会话失败: {str(e)}'
        }), 500


@app.route('/api/health', methods=['GET'])
def api_health():
    """
    健康检查端点
    
    Returns:
        健康状态
    """
    current_agent = get_or_create_agent()
    agent_status = get_agent_init_status()
    stats = get_request_stats()
    app_config = {}
    config_path = os.path.join(project_root, "config", "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            app_config = json.load(file)
    except Exception:
        app_config = {}
    
    vue_available = _vue_build_available()
    health_status = {
        'status': 'initializing',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'services': {},
        'demo_links': {
            'web_frontend': '/vue/',
            'chat': '/vue/chat',
            'knowledge_graph': '/vue/knowledge-graph',
            'topic_recommendation': '/vue/topic-recommendation',
        }
    }
    health_status['services']['web_session'] = {
        'active_sessions': stats.get('active_sessions', 0),
        'session_storage': stats.get('session_storage', 'memory'),
        'redis_sessions': stats.get('redis_sessions')
    }
    redis_config = app_config.get('redis', {})
    neo4j_config = app_config.get('neo4j', {})
    redis_runtime = stats.get('redis_sessions') or {}
    redis_available = bool(redis_runtime.get('available'))
    neo4j_configured = bool(
        neo4j_config.get('uri')
        and neo4j_config.get('username')
        and neo4j_config.get('password')
        and not str(neo4j_config.get('password')).startswith('your_')
    )
    health_status['services']['infrastructure'] = {
        'redis': {
            'configured': bool(redis_config.get('url')),
            'url': redis_config.get('url', 'not_configured'),
            'python_client_installed': importlib.util.find_spec('redis') is not None,
            'runtime_storage': stats.get('session_storage', 'memory'),
            'available': redis_available,
            'required': True,
            'deployment_ready': redis_available,
            'mode': 'redis' if redis_available else 'redis_unavailable',
            'last_error': redis_runtime.get('last_error'),
        },
        'neo4j': {
            'configured': neo4j_configured,
            'uri': neo4j_config.get('uri', 'not_configured'),
            'database': neo4j_config.get('database', 'neo4j'),
            'python_driver_installed': importlib.util.find_spec('neo4j') is not None,
            'required': True,
            'deployment_ready': False,
            'mode': 'checking' if neo4j_configured else 'neo4j_unconfigured',
        },
        'vue_frontend': {
            'build_available': vue_available,
            'required': True,
            'deployment_ready': vue_available,
            'route': '/vue/'
        }
    }
    health_status['services']['agent'] = {
        'initialized': bool(current_agent and current_agent.is_initialized),
        'initializing': agent_status.get('initializing', False),
        'error': agent_status.get('error')
    }
    if current_agent and current_agent.is_initialized:
        status = current_agent.get_status()
        health_status['services']['models'] = status.get('models', {})
        health_status['services']['redis_context'] = status.get('context', {})
    try:
        from app.modules.knowledge_graph.api import kg_service
        health_status['services']['knowledge_graph'] = kg_service.get_status()
        health_status['services']['infrastructure']['neo4j']['deployment_ready'] = (
            health_status['services']['knowledge_graph'].get('storage') == 'neo4j'
        )
        health_status['services']['infrastructure']['neo4j']['mode'] = (
            'neo4j'
            if health_status['services']['infrastructure']['neo4j']['deployment_ready']
            else 'neo4j_unavailable'
        )
    except Exception as exc:
        health_status['services']['knowledge_graph'] = {
            'storage': 'unavailable',
            'error': str(exc),
        }
    deployment_ready = all(
        [
            bool(current_agent and current_agent.is_initialized),
            redis_available,
            health_status['services']['infrastructure']['neo4j']['deployment_ready'],
            vue_available,
        ]
    )
    health_status['deployment_ready'] = deployment_ready
    health_status['status'] = 'healthy' if deployment_ready else 'degraded'
    
    return jsonify(health_status), 200


# ==================== 选题推荐API ====================

try:
    from app.modules.topic_recommendation import topic_bp
    app.register_blueprint(topic_bp)
except Exception as e:
    log_manager.error(f"选题推荐API初始化失败: {e}")

try:
    from app.modules.knowledge_graph import kg_bp
    app.register_blueprint(kg_bp)
except Exception as e:
    log_manager.error(f"知识图谱API初始化失败: {e}")




# ==================== WebSocket事件处理 ====================

@socketio.on('connect')
def handle_connect():
    """处理客户端连接"""
    # 仅在调试模式下打印连接信息
    # print(f'客户端已连接: {request.sid}')
    emit('connected', {
        'message': '连接成功',
        'sid': request.sid,
        'timestamp': datetime.now().isoformat()
    })


@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开连接"""
    # 仅在调试模式下打印断开连接信息
    # print(f'客户端断开连接: {request.sid}')
    pass


@socketio.on('chat_message')
@require_agent
def handle_chat_message(data):
    """
    处理聊天消息（流式输出）
    
    Args:
        data: 包含message, session_id, settings等字段
    """
    try:
        user_input = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        settings = data.get('settings', {})
        
        if not user_input:
            emit('error', {'message': '消息不能为空'})
            return
        
        if len(user_input) > 2000:
            emit('error', {'message': '消息长度超过限制（最大2000字符）'})
            return
        
        # 获取用户会话
        user_session = get_user_session(session_id)
        user_id = user_session['user_id']
        
        # 获取智能体
        current_agent = get_or_create_agent()
        
        # 添加到历史记录
        user_session['chat_history'].append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().isoformat()
        })
        
        # 发送开始消息
        emit('stream_start', {'message': '开始生成响应'})
        
        # 流式处理
        start_time = time.time()
        full_response = ""
        
        chunk_size = settings.get('chunk_size', 10)
        delay = settings.get('delay', 0.05)
        
        for chunk in current_agent.stream_process_user_input(
            user_input,
            user_id,
            stream_chunk_size=chunk_size,
            stream_delay=delay
        ):
            full_response += chunk
            emit('stream_chunk', {'chunk': chunk})
        
        response_time = time.time() - start_time
        
        # 添加到历史记录
        user_session['chat_history'].append({
            'role': 'assistant',
            'content': full_response,
            'timestamp': datetime.now().isoformat(),
            'response_time': response_time
        })
        
        # 更新统计
        user_session['stats']['message_count'] += 1
        user_session['stats']['total_response_time'] += response_time
        increment_message_count()
        
        # 发送结束消息
        emit('stream_end', {
            'full_response': full_response,
            'response_time': round(response_time, 3)
        })
    
    except Exception as e:
        # 仅在调试模式下打印详细错误信息
        # print(f"处理WebSocket消息时发生错误: {str(e)}")
        emit('error', {'message': '处理消息时发生错误'})


@socketio.on('get_status')
def handle_get_status():
    """获取系统状态"""
    current_agent = get_or_create_agent()
    agent_status = get_agent_init_status()
    
    if current_agent and current_agent.is_initialized:
        status = current_agent.get_status()
        emit('status_update', {
            'status': 'ready',
            'agent_initialized': True,
            'models': status.get('models', {}),
            'document_retrieval': status.get('document_retrieval', {}),
            'timestamp': datetime.now().isoformat()
        })
    else:
        emit('status_update', {
            'status': 'initializing',
            'agent_initialized': False,
            'error': agent_status.get('error'),
            'timestamp': datetime.now().isoformat()
        })


@socketio.on('ping')
def handle_ping():
    """处理ping请求"""
    emit('pong', {'timestamp': datetime.now().isoformat()})


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': '请求的资源不存在',
            'path': request.path
        }), 404
    return redirect('/vue/')


@app.errorhandler(405)
def method_not_allowed(error):
    """处理405错误"""
    return jsonify({
        'success': False,
        'error': '请求方法不允许',
        'method': request.method
    }), 405


@app.errorhandler(500)
def internal_error(error):
    """处理500错误"""
    return error_response('服务器内部错误', 500)


@app.errorhandler(Exception)
def handle_uncaught_exception(error):
    """处理所有未捕获的异常"""
    # 仅在调试模式下打印详细错误信息
    # print(f"未捕获的异常: {str(error)}")
    return error_response('服务器发生错误', 500)


# ==================== 定时任务 ====================

def start_cleanup_scheduler():
    """启动清理定时器"""
    def cleanup_task():
        while True:
            time.sleep(3600)  # 每小时执行一次
            try:
                cleanup_old_sessions(max_age_hours=24)
            except Exception as e:
                # 仅在调试模式下打印详细错误信息
                # print(f"清理任务执行失败: {e}")
                pass
    
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()


# ==================== 主程序入口 ====================

if __name__ == '__main__':
    print("智能科研选题助手 - Web应用")
    print("=" * 60)
    
    # 启动清理定时器
    start_cleanup_scheduler()
    
    # 预初始化智能体（在后台线程中）
    def init_agent():
        get_or_create_agent()
    
    init_thread = threading.Thread(target=init_agent, daemon=True)
    init_thread.start()
    
    print("正在启动Web服务器...")
    print("访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    # 启动服务器
    try:
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=5000, 
            debug=False,  # 生产环境设为False
            use_reloader=False,  # 避免重复初始化
            log_output=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 服务器已停止")
        print("感谢使用智能科研选题助手！")
