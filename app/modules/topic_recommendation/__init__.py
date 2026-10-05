# -*- coding: utf-8 -*-
"""
选题推荐参考数据库系统模块

提供大模型选题推荐参考的数据库功能，包括数据存储、查询检索和更新维护
"""

from .database import TopicDatabase
from .api import topic_bp
from .stage_based import StageBasedRecommender
from .multi_feature_algorithm import MultiFeatureRecommender

__all__ = ['TopicDatabase', 'topic_bp', 'StageBasedRecommender', 'MultiFeatureRecommender']
