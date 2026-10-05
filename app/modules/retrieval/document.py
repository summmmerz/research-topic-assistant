#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档检索器模块

负责构建文件资料索引与检索
"""

from typing import Dict, List, Any, Optional
import re
import time
import os
import json
from collections import defaultdict
import jieba
from app.utils.base import BaseModule


class DocumentRetriever(BaseModule):
    """
    文档检索器类
    """
    
    def __init__(self, config: Dict[str, Any], error_handler: Any, logger: Any):
        """
        初始化文档检索器
        
        Args:
            config: 配置参数
            error_handler: 错误处理器
            logger: 日志记录器
        """
        super().__init__(config, error_handler, logger)
        
        # 配置
        self.config = {
            "document_dir": config.get("document_dir", "data/documents"),  # 文档目录
            "index_file": config.get("index_file", "data/indexes/document_index.json"),  # 索引文件
            "max_results": config.get("max_results", 5),  # 最大结果数
            "min_similarity": config.get("min_similarity", 0.1),  # 最小相似度
            "auto_build_index": config.get("auto_build_index", False),  # 自动构建索引
            "supported_extensions": config.get("supported_extensions", [".txt", ".md", ".json"]),  # 支持的文件扩展名
        }
        
        # 索引
        self.index = {
            "documents": {},  # 文档信息
            "terms": defaultdict(list),  # 词项索引
            "tf": defaultdict(dict),  # 词频
            "df": defaultdict(int),  # 文档频率
            "idf": defaultdict(float),  # 逆文档频率
        }
        
        # 文档数量
        self.document_count = 0
        
        # 确保目录存在
        os.makedirs(self.config["document_dir"], exist_ok=True)
        os.makedirs(os.path.dirname(self.config["index_file"]), exist_ok=True)
    
    def initialize(self):
        """
        初始化文档检索器
        """
        try:
            self.logger.info("开始初始化文档检索器...")
            
            # 自动构建索引
            if self.config["auto_build_index"]:
                self.build_index()
            
            self.logger.info("文档检索器初始化完成")
        except Exception as e:
            self.error_handler.handle_error(e, "初始化文档检索器失败")
    
    def build_index(self):
        """
        构建文档索引
        """
        try:
            self.logger.info("开始构建文档索引...")
            
            with self.lock:
                # 重置索引
                self.index = {
                    "documents": {},
                    "terms": defaultdict(list),
                    "tf": defaultdict(dict),
                    "df": defaultdict(int),
                    "idf": defaultdict(float),
                }
                
                # 遍历文档目录
                documents = []
                for root, dirs, files in os.walk(self.config["document_dir"]):
                    for file in files:
                        # 检查文件扩展名
                        if any(file.endswith(ext) for ext in self.config["supported_extensions"]):
                            file_path = os.path.join(root, file)
                            documents.append(file_path)
                
                # 处理文档
                for doc_id, file_path in enumerate(documents):
                    try:
                        # 读取文档内容
                        content = self._read_document(file_path)
                        
                        # 提取关键词
                        keywords = self._extract_keywords(content)
                        
                        # 计算词频
                        tf = self._calculate_tf(keywords)
                        
                        # 更新索引
                        self.index["documents"][doc_id] = {
                            "id": doc_id,
                            "path": file_path,
                            "filename": os.path.basename(file_path),
                            "content": content[:1000],  # 保存前1000个字符作为摘要
                            "length": len(content),
                            "timestamp": time.time(),
                        }
                        
                        # 更新词项索引和文档频率
                        for term, freq in tf.items():
                            self.index["terms"][term].append(doc_id)
                            self.index["tf"][term][doc_id] = freq
                            self.index["df"][term] += 1
                        
                        self.document_count += 1
                        
                    except Exception as e:
                        self.logger.warning(f"处理文档 {file_path} 失败: {str(e)}")
                
                # 计算逆文档频率
                if self.document_count > 0:
                    for term, df in self.index["df"].items():
                        self.index["idf"][term] = max(0.1, (self.document_count / (df + 1)))
                
                # 保存索引
                self.save_index()
                
                self.logger.info(f"文档索引构建完成，共处理 {self.document_count} 个文档")
        except Exception as e:
            self.error_handler.handle_error(e, "构建文档索引失败")
    
    def retrieve(self, query: str, context: List[Dict[str, str]] = None, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            context: 上下文
            max_results: 最大结果数
            
        Returns:
            相关文档列表
        """
        try:
            self.logger.info(f"检索文档: {query[:50]}...")
            
            if max_results is None:
                max_results = self.config["max_results"]
            
            # 提取查询关键词
            query_keywords = self._extract_keywords(query)
            
            # 计算查询词频
            query_tf = self._calculate_tf(query_keywords)
            
            # 计算文档相似度
            similarities = {}
            for doc_id in self.index["documents"]:
                similarity = self._calculate_similarity(query_tf, doc_id)
                if similarity >= self.config["min_similarity"]:
                    similarities[doc_id] = similarity
            
            # 排序并返回结果
            sorted_docs = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:max_results]
            
            # 构建结果
            results = []
            for doc_id, similarity in sorted_docs:
                doc_info = self.index["documents"][doc_id]
                results.append({
                    "id": doc_id,
                    "filename": doc_info["filename"],
                    "path": doc_info["path"],
                    "content": doc_info["content"],
                    "similarity": similarity,
                    "length": doc_info["length"],
                })
            
            self.logger.info(f"检索完成，找到 {len(results)} 个相关文档")
            return results
        except Exception as e:
            self.error_handler.handle_error(e, "检索文档失败")
            return []
    
    def _read_document(self, file_path: str) -> str:
        """
        读取文档内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档内容
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"读取文档 {file_path} 失败: {str(e)}")
            return ""
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词
        
        Args:
            text: 文本
            
        Returns:
            关键词列表
        """
        # 去除标点符号和特殊字符
        text = re.sub(r"[\s\p{P}\p{S}]+", " ", text)
        
        # 使用jieba分词
        keywords = jieba.cut_for_search(text)
        
        # 过滤停用词和短词
        stop_words = set(["的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"])
        filtered_keywords = [kw for kw in keywords if kw not in stop_words and len(kw) > 1]
        
        return filtered_keywords
    
    def _calculate_tf(self, keywords: List[str]) -> Dict[str, float]:
        """
        计算词频
        
        Args:
            keywords: 关键词列表
            
        Returns:
            词频字典
        """
        tf = defaultdict(int)
        total_terms = len(keywords)
        
        # 统计词频
        for term in keywords:
            tf[term] += 1
        
        # 归一化
        if total_terms > 0:
            for term, freq in tf.items():
                tf[term] = freq / total_terms
        
        return dict(tf)
    
    def _calculate_similarity(self, query_tf: Dict[str, float], doc_id: int) -> float:
        """
        计算查询与文档的相似度
        
        Args:
            query_tf: 查询词频
            doc_id: 文档ID
            
        Returns:
            相似度
        """
        similarity = 0.0
        
        # 计算余弦相似度
        dot_product = 0.0
        query_norm = 0.0
        doc_norm = 0.0
        
        # 计算点积和查询向量范数
        for term, tf in query_tf.items():
            query_norm += tf ** 2
            if doc_id in self.index["tf"].get(term, {}):
                term_idf = self.index["idf"].get(term, 0.1)
                dot_product += tf * self.index["tf"][term][doc_id] * term_idf
        
        # 计算文档向量范数
        doc_tf = {}
        for term, docs in self.index["terms"].items():
            if doc_id in docs:
                doc_tf[term] = self.index["tf"][term][doc_id]
        
        for term, tf in doc_tf.items():
            term_idf = self.index["idf"].get(term, 0.1)
            doc_norm += (tf * term_idf) ** 2
        
        # 计算余弦相似度
        if query_norm > 0 and doc_norm > 0:
            similarity = dot_product / (query_norm ** 0.5 * doc_norm ** 0.5)
        
        return similarity
    
    def save_index(self):
        """
        保存索引
        """
        try:
            with open(self.config["index_file"], "w", encoding="utf-8") as f:
                # 将defaultdict转换为dict
                index_to_save = {
                    "documents": self.index["documents"],
                    "terms": dict(self.index["terms"]),
                    "tf": dict(self.index["tf"]),
                    "df": dict(self.index["df"]),
                    "idf": dict(self.index["idf"]),
                    "document_count": self.document_count,
                    "timestamp": time.time(),
                }
                json.dump(index_to_save, f, ensure_ascii=False, indent=2)
            
            self.logger.info("索引保存完成")
        except Exception as e:
            self.error_handler.handle_error(e, "保存索引失败")
    
    def load_index(self):
        """
        加载索引
        """
        try:
            if os.path.exists(self.config["index_file"]):
                with open(self.config["index_file"], "r", encoding="utf-8") as f:
                    loaded_index = json.load(f)
                
                # 恢复索引
                self.index = {
                    "documents": loaded_index["documents"],
                    "terms": defaultdict(list, loaded_index["terms"]),
                    "tf": defaultdict(dict, loaded_index["tf"]),
                    "df": defaultdict(int, loaded_index["df"]),
                    "idf": defaultdict(float, loaded_index["idf"]),
                }
                
                self.document_count = loaded_index.get("document_count", 0)
                
                self.logger.info(f"索引加载完成，包含 {self.document_count} 个文档")
            else:
                self.logger.warning("索引文件不存在")
        except Exception as e:
            self.error_handler.handle_error(e, "加载索引失败")
    
    def add_document(self, file_path: str) -> bool:
        """
        添加文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否添加成功
        """
        try:
            with self.lock:
                # 检查文件扩展名
                if not any(file_path.endswith(ext) for ext in self.config["supported_extensions"]):
                    self.logger.warning(f"不支持的文件扩展名: {file_path}")
                    return False
                
                # 读取文档内容
                content = self._read_document(file_path)
                
                # 提取关键词
                keywords = self._extract_keywords(content)
                
                # 计算词频
                tf = self._calculate_tf(keywords)
                
                # 生成文档ID
                doc_id = self.document_count
                
                # 更新索引
                self.index["documents"][doc_id] = {
                    "id": doc_id,
                    "path": file_path,
                    "filename": os.path.basename(file_path),
                    "content": content[:1000],
                    "length": len(content),
                    "timestamp": time.time(),
                }
                
                # 更新词项索引和文档频率
                for term, freq in tf.items():
                    self.index["terms"][term].append(doc_id)
                    self.index["tf"][term][doc_id] = freq
                    if doc_id not in [d for d, _ in self.index["terms"][term]]:
                        self.index["df"][term] += 1
                
                # 更新文档数量
                self.document_count += 1
                
                # 重新计算逆文档频率
                if self.document_count > 0:
                    for term, df in self.index["df"].items():
                        self.index["idf"][term] = max(0.1, (self.document_count / (df + 1)))
                
                # 保存索引
                self.save_index()
                
                self.logger.info(f"文档添加成功: {file_path}")
                return True
        except Exception as e:
            self.error_handler.handle_error(e, f"添加文档 {file_path} 失败")
            return False
    
    def remove_document(self, doc_id: int) -> bool:
        """
        移除文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            是否移除成功
        """
        try:
            with self.lock:
                if doc_id not in self.index["documents"]:
                    self.logger.warning(f"文档不存在: {doc_id}")
                    return False
                
                # 获取文档信息
                doc_info = self.index["documents"][doc_id]
                
                # 从索引中移除
                del self.index["documents"][doc_id]
                
                # 更新词项索引和文档频率
                terms_to_update = []
                for term, docs in self.index["terms"].items():
                    if doc_id in docs:
                        docs.remove(doc_id)
                        del self.index["tf"][term][doc_id]
                        self.index["df"][term] = len(docs)
                        terms_to_update.append(term)
                
                # 重新计算逆文档频率
                if self.document_count > 0:
                    for term in terms_to_update:
                        self.index["idf"][term] = max(0.1, (self.document_count - 1) / (self.index["df"][term] + 1))
                
                # 更新文档数量
                self.document_count -= 1
                
                # 保存索引
                self.save_index()
                
                self.logger.info(f"文档移除成功: {doc_info['filename']}")
                return True
        except Exception as e:
            self.error_handler.handle_error(e, f"移除文档 {doc_id} 失败")
            return False
    
    def update_config(self, config: Dict[str, Any]):
        """
        更新配置
        
        Args:
            config: 新配置
        """
        try:
            self.logger.info("更新文档检索器配置")
            
            with self.lock:
                self.config.update(config)
                
                # 确保目录存在
                os.makedirs(self.config["document_dir"], exist_ok=True)
                os.makedirs(os.path.dirname(self.config["index_file"]), exist_ok=True)
                
            self.logger.info("文档检索器配置更新完成")
        except Exception as e:
            self.error_handler.handle_error(e, "更新文档检索器配置失败")
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取状态
        
        Returns:
            状态信息
        """
        return {
            "document_count": self.document_count,
            "term_count": len(self.index["terms"]),
            "supported_extensions": self.config["supported_extensions"],
            "document_dir": self.config["document_dir"],
        }
    
    def shutdown(self):
        """
        关闭文档检索器
        """
        self.logger.info("关闭文档检索器")
        # 保存索引
        self.save_index()
