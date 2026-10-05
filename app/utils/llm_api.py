#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大语言模型API封装器模块

负责与各种大语言模型API进行交互
"""

import requests
import json
import time
import os
from typing import Dict, List, Any, Optional

# 尝试导入dotenv库
try:
    from dotenv import load_dotenv
    # 加载.env文件
    load_dotenv()
except ImportError:
    print("警告: dotenv库未安装，将从系统环境变量中读取API密钥")


class LLMAPIWrapper:
    """
    大语言模型API封装器
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化API封装器
        
        Args:
            config: API配置字典
        """
        self.config = config
        self.provider = config.get("provider", "openai")
        self.model = config.get("model", "gpt-3.5-turbo")
        # 优先从环境变量中读取API密钥
        self.api_key = self._get_api_key_from_env()
        # 如果环境变量中没有，再从配置文件中读取
        if not self.api_key:
            self.api_key = config.get("api_key", "")
        # 验证API密钥
        if not self.api_key:
            # 仅在调试模式下警告，不抛出异常
            print(f"警告: 未配置{self.provider.upper()} API密钥，请在.env文件中设置{self.provider.upper()}_API_KEY")
            # 继续运行，但某些功能可能不可用
            self.api_key = "dummy_api_key"
        self.max_tokens = config.get("max_tokens", 2048)
        self.temperature = config.get("temperature", 0.7)
        
        # 根据提供商设置API端点
        self.api_endpoints = {
            "openai": "https://api.openai.com/v1/chat/completions",
            "anthropic": "https://api.anthropic.com/v1/messages",
            "huggingface": "https://api-inference.huggingface.co/models/{model}",
            "deepseek": "https://api.deepseek.com/v1/chat/completions"
        }
        
        self.headers = self._get_headers()
    
    def _get_api_key_from_env(self) -> str:
        """
        从环境变量中获取API密钥
        
        Returns:
            API密钥
        """
        # 尝试不同的环境变量名称
        env_keys = [
            f"{self.provider.upper()}_API_KEY",
            "API_KEY",  # 通用API密钥
            f"{self.provider}_API_KEY"  # 小写提供商名称
        ]
        
        for key in env_keys:
            api_key = os.environ.get(key)
            if api_key:
                return api_key
        
        return ""
    
    def _get_headers(self) -> Dict[str, str]:
        """
        获取API请求头
        
        Returns:
            请求头字典
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.provider == "openai":
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self.provider == "anthropic":
            headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = "2023-06-01"
        elif self.provider == "huggingface":
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self.provider == "deepseek":
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送API请求
        
        Args:
            endpoint: API端点
            payload: 请求负载
            
        Returns:
            API响应
        """
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 429:  # Rate limit exceeded
                retry_after = int(e.response.headers.get("Retry-After", 60))
                print(f"API速率限制已达，{retry_after}秒后重试...")
                time.sleep(retry_after)
                raise
            else:
                if e.response:
                    print(f"API请求失败: {e.response.status_code} - {e.response.text}")
                else:
                    print(f"API请求失败: {str(e)}")
                raise
        except requests.exceptions.Timeout as e:
            print(f"API请求超时: {str(e)}")
            raise
        except Exception as e:
            print(f"API请求异常: {str(e)}")
            raise
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        与大语言模型对话
        
        Args:
            messages: 对话历史，格式为 [{"role": "user", "content": "..."}, ...]
            **kwargs: 额外参数
            
        Returns:
            对话响应
        """
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        
        if self.provider == "openai":
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            endpoint = self.api_endpoints[self.provider]
        elif self.provider == "anthropic":
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            endpoint = self.api_endpoints[self.provider]
        elif self.provider == "huggingface":
            payload = {
                "inputs": messages[-1]["content"],
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature
                }
            }
            endpoint = self.api_endpoints[self.provider].format(model=self.model)
        elif self.provider == "deepseek":
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            endpoint = self.api_endpoints[self.provider]
        else:
            raise ValueError(f"不支持的API提供商: {self.provider}")
        
        response = self._make_request(endpoint, payload)
        return self._parse_chat_response(response)
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        生成内容
        
        Args:
            prompt: 提示词
            **kwargs: 额外参数
            
        Returns:
            生成的内容
        """
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        
        if self.provider == "openai":
            messages = [{"role": "user", "content": prompt}]
            return self.chat(messages, max_tokens=max_tokens, temperature=temperature)
        elif self.provider == "anthropic":
            messages = [{"role": "user", "content": prompt}]
            return self.chat(messages, max_tokens=max_tokens, temperature=temperature)
        elif self.provider == "huggingface":
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature
                }
            }
            endpoint = self.api_endpoints[self.provider].format(model=self.model)
            response = self._make_request(endpoint, payload)
            return self._parse_generate_response(response)
        elif self.provider == "deepseek":
            messages = [{"role": "user", "content": prompt}]
            return self.chat(messages, max_tokens=max_tokens, temperature=temperature)
        else:
            raise ValueError(f"不支持的API提供商: {self.provider}")
    
    def _parse_chat_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析聊天响应
        
        Args:
            response: API响应
            
        Returns:
            解析后的响应
        """
        if self.provider == "openai":
            return {
                "content": response["choices"][0]["message"]["content"],
                "usage": response["usage"],
                "raw_response": response
            }
        elif self.provider == "anthropic":
            return {
                "content": response["content"][0]["text"],
                "usage": response["usage"],
                "raw_response": response
            }
        elif self.provider == "huggingface":
            return {
                "content": response[0]["generated_text"],
                "raw_response": response
            }
        elif self.provider == "deepseek":
            return {
                "content": response["choices"][0]["message"]["content"],
                "usage": response["usage"],
                "raw_response": response
            }
        else:
            return {"raw_response": response}
    
    def _parse_generate_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析生成响应
        
        Args:
            response: API响应
            
        Returns:
            解析后的响应
        """
        if self.provider == "huggingface":
            return {
                "content": response[0]["generated_text"],
                "raw_response": response
            }
        else:
            return {"raw_response": response}
    
    def set_model(self, model: str) -> None:
        """
        设置模型
        
        Args:
            model: 模型名称
        """
        self.model = model
    
    def set_temperature(self, temperature: float) -> None:
        """
        设置生成温度
        
        Args:
            temperature: 温度值 (0.0-2.0)
        """
        self.temperature = max(0.0, min(2.0, temperature))
    
    def set_max_tokens(self, max_tokens: int) -> None:
        """
        设置最大生成 tokens
        
        Args:
            max_tokens: 最大 tokens 数
        """
        self.max_tokens = max(1, max_tokens)
    
    def stream_chat(self, messages: List[Dict[str, str]], **kwargs):
        """
        流式与大语言模型对话
        
        Args:
            messages: 对话历史，格式为 [{"role": "user", "content": "..."}, ...]
            **kwargs: 额外参数
                - stream_chunk_size: 流式输出的块大小
                - stream_delay: 流式输出的延迟时间（秒）
        
        Yields:
            生成的文本片段
        """
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        stream_chunk_size = kwargs.get("stream_chunk_size", 10)
        stream_delay = kwargs.get("stream_delay", 0.05)
        
        if self.provider == "openai":
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True
            }
            endpoint = self.api_endpoints[self.provider]
        elif self.provider == "deepseek":
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True
            }
            endpoint = self.api_endpoints[self.provider]
        else:
            # 其他提供商暂不支持流式输出
            # 回退到非流式输出
            response = self.chat(messages, max_tokens=max_tokens, temperature=temperature)
            yield response.get("content", "")
            return
        
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=60
            )
            response.raise_for_status()
            
            # 处理流式响应
            buffer = ""
            for chunk in response.iter_lines():
                if chunk:
                    # 移除字节前缀并解析JSON
                    chunk = chunk.decode('utf-8')
                    if chunk.startswith('data: '):
                        chunk = chunk[6:]
                        if chunk == '[DONE]':
                            break
                        try:
                            data = json.loads(chunk)
                            if 'choices' in data:
                                choice = data['choices'][0]
                                if 'delta' in choice:
                                    delta = choice['delta']
                                    if 'content' in delta:
                                        content = delta['content']
                                        buffer += content
                                        # 当缓冲区达到指定大小时， yield 内容
                                        if len(buffer) >= stream_chunk_size:
                                            yield buffer
                                            buffer = ""
                                            time.sleep(stream_delay)
                        except json.JSONDecodeError:
                            continue
            
            #  yield 剩余内容
            if buffer:
                yield buffer
                time.sleep(stream_delay)
                
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 429:  # Rate limit exceeded
                retry_after = int(e.response.headers.get("Retry-After", 60))
                print(f"API速率限制已达，{retry_after}秒后重试...")
                time.sleep(retry_after)
                raise
            else:
                if e.response:
                    print(f"API请求失败: {e.response.status_code} - {e.response.text}")
                else:
                    print(f"API请求失败: {str(e)}")
                raise
        except requests.exceptions.Timeout as e:
            print(f"API请求超时: {str(e)}")
            raise
        except Exception as e:
            print(f"API请求异常: {str(e)}")
            raise
