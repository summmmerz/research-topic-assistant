#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中与知识图谱相关的表结构
"""

import sqlite3
import os

# 获取项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(project_root, 'app', 'data', 'topic_recommendation.db')

def check_database():
    """检查数据库中的表结构"""
    print(f"检查数据库: {db_path}")
    
    if not os.path.exists(db_path):
        print("数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\n数据库中的表:")
        for table in tables:
            table_name = table[0]
            print(f"- {table_name}")
            
            # 检查是否与知识图谱相关
            if 'graph' in table_name.lower() or 'knowledge' in table_name.lower():
                print(f"  [知识图谱相关表]")
                
                # 获取表结构
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                print("  表结构:")
                for column in columns:
                    print(f"    {column[1]} ({column[2]})")
                
                # 检查数据量
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"  数据量: {count} 条")
        
        conn.close()
        print("\n检查完成")

    except Exception as e:
        print(f"检查数据库时出错: {e}")

if __name__ == "__main__":
    check_database()
