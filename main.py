#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统主入口文件

用于启动智能科研选题助手系统
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.agent import CoreAgent


def main():
    """
    主函数
    """
    try:
        print("启动智能科研选题助手系统...")
        
        # 初始化核心智能体
        agent = CoreAgent(config_path="config/config.json")
        
        # 测试系统功能
        test_system(agent)
        
        print("系统启动成功！")
        
        # 运行交互式对话
        run_interactive_mode(agent)
        
    except Exception as e:
        print(f"系统启动失败: {str(e)}")
        sys.exit(1)


def test_system(agent):
    """
    测试系统功能
    
    Args:
        agent: 核心智能体实例
    """
    print("\n开始测试系统功能...")
    
    # 测试配置加载
    print("1. 测试配置加载...")
    config = agent.config_manager.get_config()
    print(f"   配置加载成功: {config['system']['name']} v{config['system']['version']}")
    
    # 测试上下文管理器
    print("2. 测试上下文管理器...")
    context = agent.context_manager.get_context("test_user")
    print(f"   上下文管理器初始化成功，当前上下文长度: {len(context)}")
    
    # 测试模型路由器
    print("3. 测试模型路由器...")
    model_config = agent.config_manager.get_model_config("main_model")
    print(f"   模型路由器初始化成功，主模型: {model_config['provider']} - {model_config['model']}")
    
    # 测试文档检索器
    print("4. 测试文档检索器...")
    document_config = agent.config_manager.get_document_config()
    print(f"   文档检索器初始化成功，文档目录: {document_config['document_dir']}")
    
    print("系统功能测试完成！")


def run_interactive_mode(agent):
    """
    运行交互式对话模式
    
    Args:
        agent: 核心智能体实例
    """
    print("\n进入交互式对话模式 (输入 'exit' 退出)")
    print("=" * 50)
    
    user_id = "default_user"
    
    while True:
        try:
            user_input = input("\n用户: ")
            
            if user_input.lower() == 'exit':
                print("系统正在关闭...")
                agent.shutdown()
                print("系统已关闭，再见！")
                break
            
            if not user_input.strip():
                continue
            
            # 处理用户输入
            print("助手: 正在处理您的请求...")
            # 使用流式输出处理用户输入
            print("助手: ", end="", flush=True)
            full_response = ""
            for chunk in agent.stream_process_user_input(user_input, user_id):
                print(chunk, end="", flush=True)
                full_response += chunk
            print()
            
        except KeyboardInterrupt:
            print("\n系统正在关闭...")
            agent.shutdown()
            print("系统已关闭，再见！")
            break
        except Exception as e:
            print(f"处理请求时发生错误: {str(e)}")
            continue


if __name__ == "__main__":
    main()
