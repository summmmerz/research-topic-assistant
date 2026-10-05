#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心智能体模块

系统的中央协调器，负责管理所有子模块
"""

from typing import Dict, List, Any, Optional
import time

from app.config.config_manager import ConfigManager
from app.utils.error import ErrorHandler
from app.utils.logger import LogManager
from app.modules.model.router import ModelRouter
from app.modules.retrieval.document import DocumentRetriever
from app.modules.response.generator import ResponseGenerator
from app.core.context import ContextManager
from app.modules.tool import ToolManager, ToolDecider, APIRequestTool, DatabaseQueryTool, LocalCommandTool, KnowledgeGraphQueryTool
from app.modules.model.intents import QUERY_KNOWLEDGE_GRAPH


class CoreAgent:
    """
    核心智能体类
    """
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        初始化核心智能体
        
        Args:
            config_path: 配置文件路径
        """
        # 初始化配置管理器
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # 初始化日志管理器
        self.log_manager = LogManager(self.config.get("log_manager", {}))
        self.log_manager.initialize()
        self.logger = self.log_manager.get_logger()
        
        # 初始化错误处理器
        self.error_handler = ErrorHandler(self.config.get("error_handler", {}), self.logger)
        
        # 初始化上下文管理器
        self.context_manager = ContextManager(self.config.get("context_manager", {}))
        
        # 初始化模型路由系统
        self.model_router = ModelRouter(
            config=self.config.get("model_router", {}),
            error_handler=self.error_handler,
            logger=self.logger
        )
        
        # 初始化文件资料检索模块
        self.document_retriever = DocumentRetriever(
            config=self.config.get("document_retriever", {}),
            error_handler=self.error_handler,
            logger=self.logger
        )
        
        # 初始化响应生成器
        self.response_generator = ResponseGenerator(
            config=self.config.get("response_generator", {}),
            error_handler=self.error_handler,
            logger=self.logger
        )
        
        # 初始化工具管理器
        self.tool_manager = ToolManager(
            config=self.config.get("tool_manager", {}),
            logger=self.logger,
            error_handler=self.error_handler
        )
        
        # 初始化工具决策器
        self.tool_decider = ToolDecider(
            tool_manager=self.tool_manager,
            logger=self.logger,
            error_handler=self.error_handler
        )
        
        # 系统状态
        self.is_initialized = False
        self.is_running = False
        
        # 初始化完成
        self._initialize()
    
    def _initialize(self):
        """
        初始化系统
        """
        try:
            self.logger.info("开始初始化核心智能体...")
            
            # 初始化各个模块
            self.model_router.initialize()
            self.document_retriever.initialize()
            
            # 加载文档索引
            if self.config.get("document_retriever", {}).get("auto_build_index", False):
                self.document_retriever.build_index()
            elif self.config.get("document_retriever", {}).get("auto_load_index", False):
                self.document_retriever.load_index()
            
            # 注册工具
            self._register_tools()
            
            self.is_initialized = True
            self.is_running = True
            
            self.logger.info("核心智能体初始化完成")
        except Exception as e:
            self.error_handler.handle_error(e, "初始化核心智能体失败")
            self.is_initialized = False
            self.is_running = False
    
    def _register_tools(self):
        """
        注册工具
        """
        try:
            # 注册API请求工具
            api_tool = APIRequestTool(
                name="api_request",
                description="用于发送API请求，获取外部数据",
                api_url="https://api.example.com",
                method="GET",
                logger=self.logger
            )
            self.tool_manager.register_tool(api_tool, permissions=["default", "admin"])
            
            # 注册数据库查询工具
            def db_connector(query, args):
                # 这里可以实现实际的数据库连接逻辑
                # 暂时返回模拟数据
                return [{"id": 1, "name": "测试数据"}]
            
            db_tool = DatabaseQueryTool(
                name="database_query",
                description="用于查询数据库，获取数据统计信息",
                db_connector=db_connector,
                logger=self.logger
            )
            self.tool_manager.register_tool(db_tool, permissions=["admin"])
            
            # 注册本地命令工具
            local_tool = LocalCommandTool(
                name="local_command",
                description="用于执行本地命令，检查系统状态",
                logger=self.logger
            )
            self.tool_manager.register_tool(local_tool, permissions=["admin"])

            kg_tool = KnowledgeGraphQueryTool(logger=self.logger)
            self.tool_manager.register_tool(kg_tool, permissions=["default", "admin"])
            
            self.logger.info("工具注册完成")
        except Exception as e:
            self.error_handler.handle_error(e, "注册工具失败")
    
    def process_user_input(self, user_input: str, user_id: str = "default") -> Dict[str, Any]:
        """
        处理用户输入
        
        Args:
            user_input: 用户输入文本
            user_id: 用户ID，用于区分不同用户的上下文
            
        Returns:
            处理结果，包含响应文本和相关信息
        """
        start_time = time.time()
        result = {}
        
        try:
            if not self.is_initialized or not self.is_running:
                raise RuntimeError("核心智能体未初始化或未运行")
            
            self.logger.info(f"处理用户输入: {user_input[:100]}...")
            
            # 更新上下文
            self.context_manager.update_context(user_id, user_input, "user")
            
            # 获取上下文
            context = self.context_manager.get_context(user_id)
            
            # 分析是否需要调用工具
            tool_analysis = self.tool_decider.analyze_user_input(user_input, context)
            
            if tool_analysis.get('need_tool'):
                # 调用工具
                tool_name = tool_analysis['tool_name']
                params = tool_analysis['params']
                
                self.logger.info(f"调用工具: {tool_name}, 参数: {params}")
                
                # 执行工具
                tool_result = self.tool_manager.execute_tool(
                    tool_name=tool_name,
                    params=params,
                    user_role="default"
                )
                
                if tool_name == "knowledge_graph_query":
                    result = self._handle_knowledge_graph_query(
                        user_input,
                        user_id,
                        context,
                        tool_result=tool_result,
                    )
                else:
                    # 处理工具执行结果
                    tool_response = self.tool_decider.handle_tool_result(tool_result, user_input)
                    
                    result = {
                        'response': tool_response,
                        'intent': 'tool_call',
                        'tool_name': tool_name,
                        'tool_result': tool_result
                    }
            else:
                # 分析用户意图
                intent = self.model_router.analyze_intent(user_input, context)
                self.logger.info(f"识别到用户意图: {intent}")
                
                # 根据意图分配任务
                if intent == "document_query":
                    # 处理文档查询
                    result = self._handle_document_query(user_input, user_id, context)
                elif intent == "general_chat":
                    # 处理日常对话
                    result = self._handle_general_chat(user_input, user_id, context)
                elif intent == "topic_generation":
                    # 处理选题生成
                    result = self._handle_topic_generation(user_input, user_id, context)
                elif intent == QUERY_KNOWLEDGE_GRAPH:
                    result = self._handle_knowledge_graph_query(user_input, user_id, context)
                else:
                    # 处理其他意图
                    result = self._handle_other_intents(user_input, user_id, context, intent)
            
            # 记录响应时间
            response_time = time.time() - start_time
            result["response_time"] = response_time
            
            # 检查响应时间是否符合要求
            max_response_time = self.config.get("core_agent", {}).get("max_response_time", 2.0)
            if response_time > max_response_time:
                self.logger.warning(f"响应时间过长: {response_time:.2f}秒，超过阈值 {max_response_time}秒")
            else:
                self.logger.info(f"响应时间: {response_time:.2f}秒")
            
            # 更新上下文
            if "response" in result:
                self.context_manager.update_context(user_id, result["response"], "assistant")
            
            return result
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "处理用户输入失败")
            error_response = "抱歉，我暂时无法处理您的请求，请稍后再试。"
            result["response"] = error_response
            result["error"] = str(e)
            result["response_time"] = time.time() - start_time
            
            # 更新上下文
            self.context_manager.update_context(user_id, error_response, "assistant")
            
            return result
    
    def _handle_document_query(self, user_input: str, user_id: str, context: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        处理文档查询
        """
        try:
            # 检索相关文档
            retrieved_docs = self.document_retriever.retrieve(user_input, context)
            
            # 生成响应
            response = self.response_generator.generate_document_response(
                user_input=user_input,
                retrieved_docs=retrieved_docs,
                context=context
            )
            
            return {
                "response": response,
                "intent": "document_query",
                "retrieved_docs": retrieved_docs
            }
        except Exception as e:
            self.error_handler.handle_error(e, "处理文档查询失败")
            # 降级处理：使用辅助模型生成响应
            return self._handle_general_chat(user_input, user_id, context)
    
    def _handle_general_chat(self, user_input: str, user_id: str, context: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        处理日常对话
        """
        try:
            # 使用辅助模型生成响应
            response = self.model_router.route_to_assistant_model(
                user_input=user_input,
                context=context
            )
            
            return {
                "response": response,
                "intent": "general_chat"
            }
        except Exception as e:
            self.error_handler.handle_error(e, "处理日常对话失败")
            # 降级处理：使用默认响应
            return {
                "response": "抱歉，我暂时无法处理您的请求，请稍后再试。",
                "intent": "general_chat",
                "error": str(e)
            }
    
    def _handle_topic_generation(self, user_input: str, user_id: str, context: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        处理选题生成
        """
        try:
            # 使用主模型生成选题
            response = self.model_router.route_to_main_model(
                user_input=user_input,
                context=context,
                task_type="topic_generation"
            )
            
            return {
                "response": response,
                "intent": "topic_generation"
            }
        except Exception as e:
            self.error_handler.handle_error(e, "处理选题生成失败")
            # 降级处理：使用默认响应
            return {
                "response": "抱歉，我暂时无法生成选题，请稍后再试。",
                "intent": "topic_generation",
                "error": str(e)
            }

    def _handle_knowledge_graph_query(
        self,
        user_input: str,
        user_id: str,
        context: List[Dict[str, str]],
        tool_result: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Query the knowledge graph before answering graph fact questions."""
        query_start = time.time()
        if tool_result is None:
            tool_result = self.tool_manager.execute_tool(
                tool_name="knowledge_graph_query",
                params={"question": user_input},
                user_role="default",
            )
        query_time = time.time() - query_start
        if not tool_result.get("success"):
            return {
                "response": f"知识图谱查询失败：{tool_result.get('error', '未知错误')}",
                "intent": QUERY_KNOWLEDGE_GRAPH,
                "tool_result": tool_result,
                "kg_query_time": query_time,
            }

        data = tool_result.get("data", {})
        results = data.get("results", []) if isinstance(data, dict) else []
        details = data.get("details", []) if isinstance(data, dict) else []
        evidence_lines = [
            f"存储后端：{data.get('storage', 'unknown') if isinstance(data, dict) else 'unknown'}",
            "检索实体：",
        ]
        for item in results[:5]:
            evidence_lines.append(f"- {item.get('label')}（{item.get('type')}，degree={item.get('degree', 0)}）")
        if details:
            evidence_lines.append("邻接证据：")
            for detail in details[:3]:
                related = "、".join(
                    node.get("label", "")
                    for node in detail.get("related_nodes", [])[:5]
                    if node.get("label")
                )
                evidence_lines.append(
                    f"- {detail.get('label')}：关键词={','.join(detail.get('keywords', [])[:6])}；相关={related}"
                )
        if not results:
            evidence_lines.append("- 未检索到直接匹配的图谱实体。")

        evidence = "\n".join(evidence_lines)
        prompt = (
            "你是研学助手，一位专业、严谨的科研选题导师。请只基于下面的知识图谱证据回答用户问题；"
            "如果证据不足，明确说明不足并给出下一步可查询方向。\n\n"
            f"用户问题：{user_input}\n\n知识图谱证据：\n{evidence}"
        )
        try:
            response = self.model_router.route_to_main_model(
                user_input=prompt,
                context=context,
                task_type=QUERY_KNOWLEDGE_GRAPH,
            )
        except Exception as exc:
            self.error_handler.handle_error(exc, "知识图谱证据回答生成失败")
            response = "已先查询知识图谱，当前可用证据如下：\n" + evidence

        self.logger.info(
            f"知识图谱查询完成: intent={QUERY_KNOWLEDGE_GRAPH}, "
            f"storage={data.get('storage') if isinstance(data, dict) else None}, "
            f"query_time={query_time:.3f}s"
        )
        return {
            "response": response,
            "intent": QUERY_KNOWLEDGE_GRAPH,
            "tool_result": tool_result,
            "kg_evidence": evidence,
            "kg_query_time": query_time,
        }
    
    def _handle_knowledge_graph_query(
        self,
        user_input: str,
        user_id: str,
        context: List[Dict[str, str]],
        tool_result: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Query the knowledge graph and return a graph-grounded answer."""
        query_start = time.time()
        if tool_result is None:
            tool_result = self.tool_manager.execute_tool(
                tool_name="knowledge_graph_query",
                params={"question": user_input},
                user_role="default",
            )
        query_time = time.time() - query_start

        if not tool_result.get("success"):
            return {
                "response": f"知识图谱查询失败：{tool_result.get('error', '未知错误')}",
                "intent": QUERY_KNOWLEDGE_GRAPH,
                "tool_result": tool_result,
                "kg_query_time": query_time,
            }

        data = tool_result.get("data", {})
        results = data.get("results", []) if isinstance(data, dict) else []
        details = data.get("details", []) if isinstance(data, dict) else []
        storage = data.get("storage", "unknown") if isinstance(data, dict) else "unknown"
        fallback_reason = data.get("fallback_reason") if isinstance(data, dict) else None

        evidence_lines = [f"存储后端：{storage}"]
        if fallback_reason:
            evidence_lines.append(f"降级原因：{fallback_reason}")
        evidence_lines.append("检索实体：")
        for item in results[:5]:
            evidence_lines.append(
                f"- {item.get('label')}（{item.get('type')}，degree={item.get('degree', 0)}）"
            )
        if details:
            evidence_lines.append("邻接证据：")
            for detail in details[:3]:
                related = "、".join(
                    node.get("label", "")
                    for node in detail.get("related_nodes", [])[:5]
                    if node.get("label")
                )
                keywords = ",".join(detail.get("keywords", [])[:6])
                evidence_lines.append(
                    f"- {detail.get('label')}：关键词={keywords}；相关={related}"
                )
        if not results:
            evidence_lines.append("- 未检索到直接匹配的图谱实体。")

        evidence = "\n".join(evidence_lines)
        prompt = (
            "你是研学助手，一位专业、严谨的科研选题导师。"
            "请只基于下面的知识图谱证据回答用户问题；"
            "如果证据不足，明确说明不足并给出下一步可查询方向。\n\n"
            f"用户问题：{user_input}\n\n知识图谱证据：\n{evidence}"
        )
        try:
            response = self.model_router.route_to_main_model(
                user_input=prompt,
                context=context,
                task_type=QUERY_KNOWLEDGE_GRAPH,
            )
        except Exception as exc:
            self.error_handler.handle_error(exc, "知识图谱证据回答生成失败")
            response = self._build_knowledge_graph_fallback_response(
                user_input=user_input,
                data=data if isinstance(data, dict) else {},
                results=results,
                details=details,
                evidence=evidence,
            )

        self.logger.info(
            f"知识图谱查询完成: intent={QUERY_KNOWLEDGE_GRAPH}, "
            f"storage={storage}, query_time={query_time:.3f}s"
        )
        return {
            "response": response,
            "intent": QUERY_KNOWLEDGE_GRAPH,
            "tool_result": tool_result,
            "kg_evidence": evidence,
            "kg_query_time": query_time,
        }

    def _build_knowledge_graph_fallback_response(
        self,
        user_input: str,
        data: Dict[str, Any],
        results: List[Dict[str, Any]],
        details: List[Dict[str, Any]],
        evidence: str,
    ) -> str:
        """Build a deterministic graph-grounded answer when the LLM is unavailable."""
        storage = data.get("storage", "unknown")
        query = data.get("query", user_input)
        labels = [item.get("label") for item in results[:5] if item.get("label")]
        relation_sentences = []
        seen = set()
        for detail in details[:4]:
            source = detail.get("label")
            for node in detail.get("related_nodes", [])[:6]:
                target = node.get("label")
                if not source or not target:
                    continue
                key = (source, target)
                if key in seen:
                    continue
                seen.add(key)
                relation_sentences.append(f"{source} 与 {target} 在图谱中存在邻接关系")

        answer_lines = [
            f"已先查询知识图谱（检索词：{query}，存储后端：{storage}）。",
        ]
        if labels:
            answer_lines.append("图谱中命中的核心实体包括：" + "、".join(labels) + "。")
        if relation_sentences:
            answer_lines.append(
                "从当前图谱证据看，主要关联是：" + "；".join(relation_sentences[:4]) + "。"
            )
        elif labels:
            answer_lines.append(
                "当前图谱能说明这些实体相关，但直接关系证据较少，适合继续补充论文、关键词和导师节点。"
            )
        else:
            answer_lines.append("当前图谱没有找到直接匹配实体，需要扩展关键词或补充图谱数据。")

        if "知识图谱" in user_input and "推荐" in user_input:
            answer_lines.append(
                "概念上，知识图谱为推荐系统提供结构化的实体、关键词、论文和导师关系；"
                "推荐系统可以利用这些关系做候选主题扩展、图结构中心性评分、导师方向匹配和推荐理由解释。"
            )
        answer_lines.append("\n可用图谱证据：\n" + evidence)
        return "\n".join(answer_lines)

    def _handle_other_intents(self, user_input: str, user_id: str, context: List[Dict[str, str]], intent: str) -> Dict[str, Any]:
        """
        处理其他意图
        """
        try:
            # 使用主模型处理其他意图
            response = self.model_router.route_to_main_model(
                user_input=user_input,
                context=context,
                task_type=intent
            )
            
            return {
                "response": response,
                "intent": intent
            }
        except Exception as e:
            self.error_handler.handle_error(e, f"处理意图 {intent} 失败")
            # 降级处理：使用默认响应
            return {
                "response": "抱歉，我暂时无法处理您的请求，请稍后再试。",
                "intent": intent,
                "error": str(e)
            }
    
    def get_context(self, user_id: str = "default") -> List[Dict[str, str]]:
        """
        获取用户上下文
        
        Args:
            user_id: 用户ID
            
        Returns:
            上下文对话历史
        """
        return self.context_manager.get_context(user_id)
    
    def clear_context(self, user_id: str = "default"):
        """
        清除用户上下文
        
        Args:
            user_id: 用户ID
        """
        self.context_manager.clear_context(user_id)
    
    def update_config(self, config: Dict[str, Any]):
        """
        更新配置
        
        Args:
            config: 新配置
        """
        try:
            self.logger.info("更新配置")
            self.config_manager.update_config(config)
            self.config = self.config_manager.get_config()
            
            # 重新初始化受影响的模块
            self.model_router.update_config(self.config.get("model_router", {}))
            self.document_retriever.update_config(self.config.get("document_retriever", {}))
            self.response_generator.update_config(self.config.get("response_generator", {}))
            self.context_manager.update_config(self.config.get("context_manager", {}))
            self.log_manager.update_config(self.config.get("log_manager", {}))
            
            self.logger.info("配置更新完成")
        except Exception as e:
            self.error_handler.handle_error(e, "更新配置失败")
    
    def shutdown(self):
        """
        关闭系统
        """
        try:
            self.logger.info("开始关闭核心智能体...")
            
            self.is_running = False
            
            # 关闭各个模块
            self.model_router.shutdown()
            self.document_retriever.shutdown()
            
            # 关闭工具管理器
            self.tool_manager.shutdown()
            
            # 保存上下文
            self.context_manager.save_contexts()
            
            # 关闭日志
            self.log_manager.shutdown()
            
            self.logger.info("核心智能体关闭完成")
        except Exception as e:
            self.error_handler.handle_error(e, "关闭核心智能体失败")
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            系统状态信息
        """
        return {
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "models": self.model_router.get_model_status(),
            "document_retrieval": self.document_retriever.get_status(),
            "context": self.context_manager.get_status(),
            "config": {
                "models": self.config.get("model_router", {}),
                "document_retrieval": self.config.get("document_retriever", {}),
                "context": self.config.get("context_manager", {}),
                "performance": self.config.get("core_agent", {})
            }
        }
    
    def stream_process_user_input(self, user_input: str, user_id: str = "default", **kwargs):
        """
        流式处理用户输入
        
        Args:
            user_input: 用户输入文本
            user_id: 用户ID，用于区分不同用户的上下文
            **kwargs: 额外参数
                - stream_chunk_size: 流式输出的块大小
                - stream_delay: 流式输出的延迟时间（秒）
        
        Yields:
            处理结果的文本片段
        """
        start_time = time.time()
        full_response = ""
        
        try:
            if not self.is_initialized or not self.is_running:
                yield "核心智能体未初始化或未运行，请稍后再试。"
                return
            
            self.logger.info(f"流式处理用户输入: {user_input[:100]}...")
            
            # 更新上下文
            self.context_manager.update_context(user_id, user_input, "user")
            
            # 获取上下文
            context = self.context_manager.get_context(user_id)
            
            # 分析用户意图
            intent = self.model_router.analyze_intent(user_input, context)
            self.logger.info(f"识别到用户意图: {intent}")
            
            # 根据意图分配任务
            if intent == "document_query":
                # 处理文档查询
                for chunk in self._stream_handle_document_query(user_input, user_id, context, **kwargs):
                    full_response += chunk
                    yield chunk
            elif intent == "general_chat":
                # 处理日常对话
                for chunk in self._stream_handle_general_chat(user_input, user_id, context, **kwargs):
                    full_response += chunk
                    yield chunk
            elif intent == "topic_generation":
                # 处理选题生成
                for chunk in self._stream_handle_topic_generation(user_input, user_id, context, **kwargs):
                    full_response += chunk
                    yield chunk
            else:
                # 处理其他意图
                for chunk in self._stream_handle_other_intents(user_input, user_id, context, intent, **kwargs):
                    full_response += chunk
                    yield chunk
            
            # 记录响应时间
            response_time = time.time() - start_time
            self.logger.info(f"流式响应时间: {response_time:.2f}秒")
            
            # 更新上下文
            if full_response:
                self.context_manager.update_context(user_id, full_response, "assistant")
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "流式处理用户输入失败")
            error_response = "抱歉，我暂时无法处理您的请求，请稍后再试。"
            yield error_response
            
            # 更新上下文
            self.context_manager.update_context(user_id, error_response, "assistant")
    
    def _stream_handle_document_query(self, user_input: str, user_id: str, context: List[Dict[str, str]], **kwargs):
        """
        流式处理文档查询
        """
        try:
            # 检索相关文档
            retrieved_docs = self.document_retriever.retrieve(user_input, context)
            
            # 生成响应
            # 这里可以根据需要实现流式响应生成
            # 暂时使用模型的流式响应
            for chunk in self.model_router.stream_route_to_assistant_model(user_input, context, **kwargs):
                yield chunk
        except Exception as e:
            self.error_handler.handle_error(e, "流式处理文档查询失败")
            # 降级处理：使用主模型生成响应
            for chunk in self._stream_handle_general_chat(user_input, user_id, context, **kwargs):
                yield chunk
    
    def _stream_handle_general_chat(self, user_input: str, user_id: str, context: List[Dict[str, str]], **kwargs):
        """
        流式处理日常对话
        """
        try:
            for chunk in self.model_router.stream_route_to_assistant_model(user_input, context, **kwargs):
                yield chunk
        except Exception as e:
            self.error_handler.handle_error(e, "流式处理日常对话失败")
            yield "抱歉，我暂时无法处理您的请求，请稍后再试。"
    
    def _stream_handle_topic_generation(self, user_input: str, user_id: str, context: List[Dict[str, str]], **kwargs):
        """
        流式处理选题生成
        """
        try:
            for chunk in self.model_router.stream_route_to_main_model(user_input, context, **kwargs):
                yield chunk
        except Exception as e:
            self.error_handler.handle_error(e, "流式处理选题生成失败")
            yield "抱歉，我暂时无法处理您的请求，请稍后再试。"
    
    def _stream_handle_other_intents(self, user_input: str, user_id: str, context: List[Dict[str, str]], intent: str, **kwargs):
        """
        流式处理其他意图
        """
        try:
            for chunk in self.model_router.stream_route_to_main_model(user_input, context, **kwargs):
                yield chunk
        except Exception as e:
            self.error_handler.handle_error(e, f"流式处理{intent}失败")
            yield "抱歉，我暂时无法处理您的请求，请稍后再试。"
