#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
响应生成器模块

负责生成最终的响应，并整合各个模块的输出
"""

from typing import Dict, List, Any, Optional
from app.utils.base import BaseModule
from app.utils.common import format_response


class ResponseGenerator(BaseModule):
    """
    响应生成器类
    """
    
    def __init__(self, config: Dict[str, Any], error_handler: Any, logger: Any):
        """
        初始化响应生成器
        
        Args:
            config: 配置参数
            error_handler: 错误处理器
            logger: 日志记录器
        """
        super().__init__(config, error_handler, logger)
        
        # 配置
        self.config = {
            "response_templates": config.get("response_templates", {}),  # 响应模板
            "max_response_length": config.get("max_response_length", 2048),  # 最大响应长度
            "min_response_length": config.get("min_response_length", 10),  # 最小响应长度
            "response_timeout": config.get("response_timeout", 30),  # 响应超时时间
        }
        
        # 响应模板
        self.response_templates = {
            "document_response": "根据查询，我找到以下相关文档：\n\n{documents}\n\n{summary}",
            "general_response": "{content}",
            "topic_response": "根据您的需求，我为您生成了以下科研选题：\n\n{topics}",
            "error_response": "抱歉，我暂时无法处理您的请求，请稍后再试。\n\n错误信息：{error}",
        }
        
        # 更新配置中的模板
        if self.config.get("response_templates"):
            self.response_templates.update(self.config["response_templates"])
    
    def generate_document_response(self, user_input: str, retrieved_docs: List[Dict[str, Any]], context: List[Dict[str, str]]) -> str:
        """
        生成文档查询响应
        
        Args:
            user_input: 用户输入
            retrieved_docs: 检索到的文档
            context: 上下文
            
        Returns:
            响应文本
        """
        try:
            self.logger.info("生成文档查询响应")
            
            # 构建文档列表
            documents_text = ""
            for i, doc in enumerate(retrieved_docs, 1):
                documents_text += f"{i}. **{doc['filename']}**\n"
                documents_text += f"   相似度: {doc['similarity']:.2f}\n"
                documents_text += f"   内容摘要: {doc['content'][:200]}...\n\n"
            
            # 生成摘要
            summary = self._generate_document_summary(user_input, retrieved_docs)
            
            # 使用模板生成响应
            response = self.response_templates["document_response"].format(
                documents=documents_text,
                summary=summary
            )
            
            # 限制响应长度
            response = self._limit_response_length(response)
            
            return response
        except Exception as e:
            self.error_handler.handle_error(e, "生成文档查询响应失败")
            return self.response_templates["error_response"].format(error=str(e))
    
    def generate_general_response(self, user_input: str, model_response: str, context: List[Dict[str, str]]) -> str:
        """
        生成一般响应
        
        Args:
            user_input: 用户输入
            model_response: 模型响应
            context: 上下文
            
        Returns:
            响应文本
        """
        try:
            self.logger.info("生成一般响应")
            
            # 使用模板生成响应
            response = self.response_templates["general_response"].format(
                content=model_response
            )
            
            # 限制响应长度
            response = self._limit_response_length(response)
            
            return response
        except Exception as e:
            self.error_handler.handle_error(e, "生成一般响应失败")
            return self.response_templates["error_response"].format(error=str(e))
    
    def generate_topic_response(self, user_input: str, topics: List[Dict[str, Any]], context: List[Dict[str, str]]) -> str:
        """
        生成选题响应
        
        Args:
            user_input: 用户输入
            topics: 生成的选题
            context: 上下文
            
        Returns:
            响应文本
        """
        try:
            self.logger.info("生成选题响应")
            
            # 构建选题列表
            topics_text = ""
            for i, topic in enumerate(topics, 1):
                topics_text += f"{i}. **{topic['title']}**\n"
                if "background" in topic and topic["background"]:
                    topics_text += f"   研究背景: {topic['background'][:150]}...\n"
                if "research_content" in topic and topic["research_content"]:
                    topics_text += f"   研究内容: {topic['research_content'][:150]}...\n"
                topics_text += "\n"
            
            # 使用模板生成响应
            response = self.response_templates["topic_response"].format(
                topics=topics_text
            )
            
            # 限制响应长度
            response = self._limit_response_length(response)
            
            return response
        except Exception as e:
            self.error_handler.handle_error(e, "生成选题响应失败")
            return self.response_templates["error_response"].format(error=str(e))
    
    def generate_error_response(self, error: Exception) -> str:
        """
        生成错误响应
        
        Args:
            error: 错误
            
        Returns:
            响应文本
        """
        try:
            self.logger.info("生成错误响应")
            
            # 使用模板生成响应
            response = self.response_templates["error_response"].format(
                error=str(error)
            )
            
            # 限制响应长度
            response = self._limit_response_length(response)
            
            return response
        except Exception as e:
            self.logger.error(f"生成错误响应失败: {str(e)}")
            return "抱歉，系统暂时无法处理您的请求，请稍后再试。"
    
    def _generate_document_summary(self, user_input: str, retrieved_docs: List[Dict[str, Any]]) -> str:
        """
        生成文档摘要
        
        Args:
            user_input: 用户输入
            retrieved_docs: 检索到的文档
            
        Returns:
            摘要文本
        """
        if not retrieved_docs:
            return "未找到相关文档。"
        
        # 简单的摘要生成
        summary = f"共找到 {len(retrieved_docs)} 个相关文档。"
        
        # 如果只有一个文档，提供更详细的摘要
        if len(retrieved_docs) == 1:
            doc = retrieved_docs[0]
            summary += f" 最相关的文档是《{doc['filename']}》，相似度为 {doc['similarity']:.2f}。"
        
        return summary
    
    def _limit_response_length(self, response: str) -> str:
        """
        限制响应长度
        
        Args:
            response: 响应文本
            
        Returns:
            限制长度后的响应
        """
        if len(response) > self.config["max_response_length"]:
            self.logger.warning(f"响应长度超过限制，从 {len(response)} 字符截断到 {self.config['max_response_length']} 字符")
        return format_response(response, self.config["max_response_length"])
    
    def update_config(self, config: Dict[str, Any]):
        """
        更新配置
        
        Args:
            config: 新配置
        """
        try:
            self.logger.info("更新响应生成器配置")
            
            with self.lock:
                self.config.update(config)
                
                # 更新模板
                if config.get("response_templates"):
                    self.response_templates.update(config["response_templates"])
            
            self.logger.info("响应生成器配置更新完成")
        except Exception as e:
            self.error_handler.handle_error(e, "更新响应生成器配置失败")
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取状态
        
        Returns:
            状态信息
        """
        return {
            "max_response_length": self.config["max_response_length"],
            "min_response_length": self.config["min_response_length"],
            "response_timeout": self.config["response_timeout"],
            "num_templates": len(self.response_templates),
        }
    
    def shutdown(self):
        """
        关闭响应生成器
        """
        self.logger.info("关闭响应生成器")
        # 响应生成器不需要特别关闭，只是释放资源
