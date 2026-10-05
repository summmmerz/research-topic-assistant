#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体管理器模块

负责管理智能体的初始化和获取。
"""

import os
import threading
from datetime import datetime
from typing import Optional

from app.core.agent import CoreAgent


agent: Optional[CoreAgent] = None
agent_lock = threading.Lock()
agent_init_status = {
    "initialized": False,
    "initializing": False,
    "error": None,
    "start_time": None,
    "last_attempt_time": None,
}


def get_or_create_agent() -> Optional[CoreAgent]:
    """
    获取或创建智能体实例。

    初始化失败时不会锁死状态，下一次调用会重新尝试。
    """
    global agent, agent_init_status

    with agent_lock:
        if agent is not None and agent.is_initialized:
            agent_init_status["initialized"] = True
            agent_init_status["initializing"] = False
            agent_init_status["error"] = None
            return agent

        now = datetime.now()
        agent_init_status["initializing"] = True
        agent_init_status["last_attempt_time"] = now
        if agent_init_status["start_time"] is None:
            agent_init_status["start_time"] = now

        try:
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            config_path = os.path.join(project_root, "config", "config.json")

            if not os.path.exists(config_path):
                agent_init_status["initialized"] = False
                agent_init_status["initializing"] = False
                agent_init_status["error"] = f"配置文件不存在: {config_path}"
                print(f"错误: {agent_init_status['error']}")
                return None

            agent = CoreAgent(config_path=config_path)

            if agent.is_initialized:
                agent_init_status["initialized"] = True
                agent_init_status["initializing"] = False
                agent_init_status["error"] = None
                print("智能体初始化成功")
                return agent

            agent_init_status["initialized"] = False
            agent_init_status["initializing"] = False
            agent_init_status["error"] = "智能体初始化失败"
            print(f"错误: {agent_init_status['error']}")
            return None

        except Exception as exc:
            agent_init_status["initialized"] = False
            agent_init_status["initializing"] = False
            agent_init_status["error"] = str(exc)
            print(f"初始化智能体失败: {exc}")
            return None


def get_agent_init_status() -> dict:
    """获取智能体初始化状态。"""
    return agent_init_status


def get_agent() -> Optional[CoreAgent]:
    """获取智能体实例，不自动创建。"""
    return agent
