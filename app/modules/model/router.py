#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型路由器模块

负责根据用户查询类型自动分配至合适的模型
"""

from typing import Dict, List, Any, Optional
import re
import time

from app.utils.llm_api import LLMAPIWrapper
from app.utils.base import BaseModule
from app.modules.model.intents import QUERY_KNOWLEDGE_GRAPH


class ModelRouter(BaseModule):
    """
    模型路由器类
    """
    
    def __init__(self, config: Dict[str, Any], error_handler: Any, logger: Any):
        """
        初始化模型路由器
        
        Args:
            config: 配置参数
            error_handler: 错误处理器
            logger: 日志记录器
        """
        super().__init__(config, error_handler, logger)
        
        # 配置
        self.config = {
            "main_model": config.get("main_model", {}),  # 主模型配置
            "assistant_model": config.get("assistant_model", {}),  # 辅助模型配置
            "intent_patterns": config.get("intent_patterns", {}),  # 意图识别模式
            "task_routing": config.get("task_routing", {}),  # 任务路由规则
            "timeout": config.get("timeout", 30),  # 超时时间
            "retry_count": config.get("retry_count", 3),  # 重试次数
        }
        
        # 模型实例
        self.main_model = None
        self.assistant_model = None
        
        # 模型状态
        self.main_model_healthy = False
        self.assistant_model_healthy = False
        
        # 意图识别模式
        self.intent_patterns = {
            "document_query": [
                r"查询.*文件",
                r"查找.*资料",
                r"搜索.*文档",
                r"读取.*文件",
                r"获取.*信息",
                r"文件.*内容",
                r"资料.*详情",
                r"文档.*信息",
            ],
            "general_chat": [
                r"你好",
                r"您好",
                r"在吗",
                r"聊天",
                r"对话",
                r"讨论",
                r"交流",
            ],
            "topic_generation": [
                r"生成.*选题",
                r"推荐.*题目",
                r"科研.*选题",
                r"研究.*方向",
                r"论文.*题目",
            ],
            QUERY_KNOWLEDGE_GRAPH: [
                r"知识图谱",
                r"图谱.*查询",
                r"查询.*关系",
                r"关联.*(实体|关键词|导师|论文|方向)",
                r".*导师.*研究.*方向",
            ],
        }
        
        # 任务路由规则
        self.task_routing = {
            "document_query": "assistant_model",
            "general_chat": "assistant_model",
            "topic_generation": "main_model",
            QUERY_KNOWLEDGE_GRAPH: "main_model",
        }
        
        # 更新配置中的模式和规则
        if self.config.get("intent_patterns"):
            self.intent_patterns.update(self.config["intent_patterns"])
        if self.config.get("task_routing"):
            self.task_routing.update(self.config["task_routing"])
    
    def initialize(self):
        """
        初始化模型路由器
        """
        try:
            self.logger.info("开始初始化模型路由器...")
            
            # 初始化主模型
            if self.config["main_model"]:
                self.logger.info(f"初始化主模型: {self.config['main_model'].get('provider')}/{self.config['main_model'].get('model')}")
                self.main_model = LLMAPIWrapper(self.config["main_model"])
                self.main_model_healthy = self._health_check(self.main_model, "main_model")
            
            # 初始化辅助模型
            if self.config["assistant_model"]:
                self.logger.info(f"初始化辅助模型: {self.config['assistant_model'].get('provider')}/{self.config['assistant_model'].get('model')}")
                self.assistant_model = LLMAPIWrapper(self.config["assistant_model"])
                self.assistant_model_healthy = self._health_check(self.assistant_model, "assistant_model")
            
            # 检查至少有一个模型可用
            if not self.main_model_healthy and not self.assistant_model_healthy:
                self.logger.error("所有模型均不可用，请检查配置")
                raise RuntimeError("所有模型均不可用")
            
            self.logger.info("模型路由器初始化完成")
        except Exception as e:
            self.error_handler.handle_error(e, "初始化模型路由器失败")
    
    def _health_check(self, model: LLMAPIWrapper, model_name: str) -> bool:
        """
        模型健康检查
        
        Args:
            model: 模型实例
            model_name: 模型名称
            
        Returns:
            是否健康
        """
        try:
            # 发送简单的健康检查请求
            messages = [{"role": "user", "content": "健康检查"}]
            response = model.chat(messages, max_tokens=10, timeout=5)
            
            if "content" in response and response["content"]:
                self.logger.info(f"{model_name} 健康检查通过")
                return True
            else:
                self.logger.warning(f"{model_name} 健康检查失败: 响应格式不正确")
                return False
        except Exception as e:
            self.logger.warning(f"{model_name} 健康检查失败: {str(e)}")
            return False
    
    def analyze_intent(self, user_input: str, context: List[Dict[str, str]]) -> str:
        """
        分析用户意图
        
        Args:
            user_input: 用户输入
            context: 上下文
            
        Returns:
            意图类型
        """
        # 简单的意图识别
        user_input_lower = user_input.lower()
        
        # 检查文档查询意图
        for pattern in self.intent_patterns.get("document_query", []):
            if re.search(pattern, user_input_lower):
                return "document_query"

        for pattern in self.intent_patterns.get(QUERY_KNOWLEDGE_GRAPH, []):
            if re.search(pattern, user_input_lower):
                return QUERY_KNOWLEDGE_GRAPH
        
        # 检查选题生成意图
        for pattern in self.intent_patterns.get("topic_generation", []):
            if re.search(pattern, user_input_lower):
                return "topic_generation"
        
        # 检查日常对话意图
        for pattern in self.intent_patterns.get("general_chat", []):
            if re.search(pattern, user_input_lower):
                return "general_chat"
        
        # 默认意图
        return "general_chat"
    
    def route_task(self, task_type: str, user_input: str, context: List[Dict[str, str]] = None) -> str:
        """
        路由任务到合适的模型
        
        Args:
            task_type: 任务类型
            user_input: 用户输入
            context: 上下文
            
        Returns:
            模型名称
        """
        # 根据任务类型路由
        model_name = self.task_routing.get(task_type, "main_model")
        
        # 检查模型是否健康
        if model_name == "main_model" and not self.main_model_healthy:
            self.logger.warning("主模型不健康，切换到辅助模型")
            model_name = "assistant_model"
        elif model_name == "assistant_model" and not self.assistant_model_healthy:
            self.logger.warning("辅助模型不健康，切换到主模型")
            model_name = "main_model"
        
        # 检查最终模型是否健康
        if model_name == "main_model" and not self.main_model_healthy:
            raise RuntimeError("所有模型均不可用")
        elif model_name == "assistant_model" and not self.assistant_model_healthy:
            raise RuntimeError("所有模型均不可用")
        
        return model_name
    
    def route_to_main_model(self, user_input: str, context: List[Dict[str, str]], **kwargs) -> str:
        """
        路由到主模型
        
        Args:
            user_input: 用户输入
            context: 上下文
            **kwargs: 额外参数
            
        Returns:
            模型响应
        """
        return self._call_model(self.main_model, "main_model", user_input, context, **kwargs)
    
    def route_to_assistant_model(self, user_input: str, context: List[Dict[str, str]], **kwargs) -> str:
        """
        路由到辅助模型
        
        Args:
            user_input: 用户输入
            context: 上下文
            **kwargs: 额外参数
            
        Returns:
            模型响应
        """
        return self._call_model(self.assistant_model, "assistant_model", user_input, context, **kwargs)
    
    def _call_model(self, model: LLMAPIWrapper, model_name: str, user_input: str, context: List[Dict[str, str]], **kwargs) -> str:
        """
        调用模型
        
        Args:
            model: 模型实例
            model_name: 模型名称
            user_input: 用户输入
            context: 上下文
            **kwargs: 额外参数
            
        Returns:
            模型响应
        """
        retry_count = 0
        last_error = None
        
        while retry_count < self.config["retry_count"]:
            try:
                self.logger.info(f"调用 {model_name} 处理任务")
                
                # 构建消息
                messages = []
                
                # 获取任务类型
                task_type = kwargs.get("task_type", "general_chat")
                
                # 添加系统提示词
                system_prompt = self._get_system_prompt(task_type)
                messages.append({"role": "system", "content": system_prompt})
                
                # 添加上下文
                if context:
                    messages.extend(context)
                else:
                    # 如果没有上下文，只添加当前输入
                    messages.append({"role": "user", "content": user_input})
                
                # 调用模型
                response = model.chat(messages, **kwargs)
                
                # 提取响应内容
                if "content" in response and response["content"]:
                    # 更新模型健康状态
                    if model_name == "main_model":
                        self.main_model_healthy = True
                    else:
                        self.assistant_model_healthy = True
                    
                    return response["content"]
                else:
                    raise ValueError("模型响应为空")
                    
            except Exception as e:
                last_error = e
                retry_count += 1
                self.logger.warning(f"调用 {model_name} 失败，重试 {retry_count}/{self.config['retry_count']}: {str(e)}")
                
                # 更新模型健康状态
                if model_name == "main_model":
                    self.main_model_healthy = False
                else:
                    self.assistant_model_healthy = False
                
                # 等待后重试
                time.sleep(1 * retry_count)
        
        # 重试失败，尝试故障转移
        self.logger.error(f"调用 {model_name} 失败，尝试故障转移")
        
        if model_name == "main_model" and self.assistant_model_healthy:
            self.logger.info("故障转移到辅助模型")
            return self._call_model(self.assistant_model, "assistant_model", user_input, context, **kwargs)
        elif model_name == "assistant_model" and self.main_model_healthy:
            self.logger.info("故障转移到主模型")
            return self._call_model(self.main_model, "main_model", user_input, context, **kwargs)
        else:
            # 所有模型都失败
            error_msg = f"所有模型均不可用: {str(last_error)}"
            self.error_handler.handle_error(last_error, error_msg)
            return "抱歉，系统暂时无法处理您的请求，请稍后再试。"
    
    def _get_system_prompt(self, task_type: str) -> str:
        """
        获取系统提示词
        
        Args:
            task_type: 任务类型
            
        Returns:
            系统提示词
        """
        prompts = {
            "general_chat": "你是一个日常对话智能体，同时也是一个友好的科研选题顾问。你擅长以自然、流畅的方式引导用户进行选题讨论。你的职责包括：1) 以友好、轻松的方式开启与选题相关的话题，让用户感到舒适；2) 通过开放式问题了解用户的兴趣领域、研究需求或学术目标；3) 基于用户反馈提供适当的选题方向建议作为参考；4) 根据用户的回应进行针对性追问，深入了解用户的具体需求；5) 帮助用户逐步聚焦并明确具体的研究选题。在整个过程中，保持对话的互动性和支持性，避免生硬的推销感，让用户感受到被理解和支持。使用通俗易懂的语言，保持友好、亲切的语气，让对话自然流畅。所有回答均需使用中文。",
            "topic_generation": "你是一个专业选题推荐智能体，专注于提供高质量的科研选题推荐服务。你具备深厚的领域知识，能够基于用户需求、兴趣偏好和当前热点趋势，提供结构化、有针对性的选题建议。你的回答应包括：选题背景分析、核心价值阐述、实施可行性评估、潜在研究方向，以及推荐理由和预期成果。请确保推荐内容具有深度、创新性和实用性，展现专业素养和学术洞察力。所有回答均需使用中文。"
            ,
            QUERY_KNOWLEDGE_GRAPH: "你是研学助手和博士生导师型智能体。请基于知识图谱查询结果回答，优先说明实体、关系和证据；图谱没有证据时明确说明不足。所有回答均需使用中文。"
        }
        
        return prompts.get(task_type, prompts["general_chat"])
    
    def update_config(self, config: Dict[str, Any]):
        """
        更新配置
        
        Args:
            config: 新配置
        """
        try:
            self.logger.info("更新模型路由器配置")
            
            with self.lock:
                # 更新配置
                self.config.update(config)
                
                # 更新意图识别模式
                if self.config.get("intent_patterns"):
                    self.intent_patterns.update(self.config["intent_patterns"])
                
                # 更新任务路由规则
                if self.config.get("task_routing"):
                    self.task_routing.update(self.config["task_routing"])
                
                # 重新初始化模型
                if self.config.get("main_model"):
                    self.main_model = LLMAPIWrapper(self.config["main_model"])
                    self.main_model_healthy = self._health_check(self.main_model, "main_model")
                
                if self.config.get("assistant_model"):
                    self.assistant_model = LLMAPIWrapper(self.config["assistant_model"])
                    self.assistant_model_healthy = self._health_check(self.assistant_model, "assistant_model")
                
            self.logger.info("模型路由器配置更新完成")
        except Exception as e:
            self.error_handler.handle_error(e, "更新模型路由器配置失败")
    
    def get_model_status(self) -> Dict[str, Any]:
        """
        获取模型状态
        
        Returns:
            模型状态
        """
        return {
            "main_model": {
                "healthy": self.main_model_healthy,
                "provider": self.config["main_model"].get("provider", "unknown") if self.config.get("main_model") else "not_configured",
                "model": self.config["main_model"].get("model", "unknown") if self.config.get("main_model") else "not_configured",
            },
            "assistant_model": {
                "healthy": self.assistant_model_healthy,
                "provider": self.config["assistant_model"].get("provider", "unknown") if self.config.get("assistant_model") else "not_configured",
                "model": self.config["assistant_model"].get("model", "unknown") if self.config.get("assistant_model") else "not_configured",
            },
        }
    
    def shutdown(self):
        """
        关闭模型路由器
        """
        self.logger.info("关闭模型路由器")
        # 模型实例不需要特别关闭，只是释放引用
        self.main_model = None
        self.assistant_model = None
        self.main_model_healthy = False
        self.assistant_model_healthy = False
    
    def stream_route_to_main_model(self, user_input: str, context: List[Dict[str, str]], **kwargs):
        """
        流式路由到主模型
        
        Args:
            user_input: 用户输入
            context: 上下文
            **kwargs: 额外参数
                - stream_chunk_size: 流式输出的块大小
                - stream_delay: 流式输出的延迟时间（秒）
        
        Yields:
            模型响应的文本片段
        """
        return self._stream_call_model(self.main_model, "main_model", user_input, context, **kwargs)
    
    def stream_route_to_assistant_model(self, user_input: str, context: List[Dict[str, str]], **kwargs):
        """
        流式路由到辅助模型
        
        Args:
            user_input: 用户输入
            context: 上下文
            **kwargs: 额外参数
                - stream_chunk_size: 流式输出的块大小
                - stream_delay: 流式输出的延迟时间（秒）
        
        Yields:
            模型响应的文本片段
        """
        return self._stream_call_model(self.assistant_model, "assistant_model", user_input, context, **kwargs)
    
    def _stream_call_model(self, model: LLMAPIWrapper, model_name: str, user_input: str, context: List[Dict[str, str]], **kwargs):
        """
        流式调用模型
        
        Args:
            model: 模型实例
            model_name: 模型名称
            user_input: 用户输入
            context: 上下文
            **kwargs: 额外参数
                - stream_chunk_size: 流式输出的块大小
                - stream_delay: 流式输出的延迟时间（秒）
        
        Yields:
            模型响应的文本片段
        """
        retry_count = 0
        last_error = None
        
        while retry_count < self.config["retry_count"]:
            try:
                self.logger.info(f"流式调用 {model_name} 处理任务")
                
                # 构建消息
                messages = []
                
                # 获取任务类型
                task_type = kwargs.get("task_type", "general_chat")
                
                # 添加系统提示词
                system_prompt = self._get_system_prompt(task_type)
                messages.append({"role": "system", "content": system_prompt})
                
                # 添加上下文
                if context:
                    messages.extend(context)
                else:
                    # 如果没有上下文，只添加当前输入
                    messages.append({"role": "user", "content": user_input})
                
                # 流式调用模型
                for chunk in model.stream_chat(messages, **kwargs):
                    # 生成响应片段
                    yield chunk
                
                # 更新模型健康状态
                if model_name == "main_model":
                    self.main_model_healthy = True
                else:
                    self.assistant_model_healthy = True
                
                return
                
            except Exception as e:
                last_error = e
                retry_count += 1
                self.logger.warning(f"流式调用 {model_name} 失败，重试 {retry_count}/{self.config['retry_count']}: {str(e)}")
                
                # 更新模型健康状态
                if model_name == "main_model":
                    self.main_model_healthy = False
                else:
                    self.assistant_model_healthy = False
                
                # 短暂延迟后重试
                time.sleep(1)
        
        # 重试失败，尝试故障转移
        self.logger.error(f"流式调用 {model_name} 失败，尝试故障转移")
        
        if model_name == "main_model" and self.assistant_model_healthy:
            self.logger.info("故障转移到辅助模型")
            return self._stream_call_model(self.assistant_model, "assistant_model", user_input, context, **kwargs)
        elif model_name == "assistant_model" and self.main_model_healthy:
            self.logger.info("故障转移到主模型")
            return self._stream_call_model(self.main_model, "main_model", user_input, context, **kwargs)
        else:
            # 所有模型都失败
            error_msg = f"所有模型均不可用: {str(last_error)}"
            self.error_handler.handle_error(last_error, error_msg)
            yield "抱歉，系统暂时无法处理您的请求，请稍后再试。"
            return
