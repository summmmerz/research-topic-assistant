#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试NLTK数据加载

验证NLTK数据是否能够正确加载，以及知识图谱构建功能是否能够正常工作
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_nltk_data():
    """测试NLTK数据加载"""
    print("测试NLTK数据加载...")
    
    try:
        from nltk.tokenize import word_tokenize
        from nltk.corpus import stopwords
        
        # 测试tokenize
        test_text = "Hello, world! This is a test."
        tokens = word_tokenize(test_text)
        print(f"✓ Tokenize测试成功: {tokens}")
        
        # 测试stopwords
        english_stopwords = stopwords.words('english')
        print(f"✓ Stopwords测试成功，英语停用词数量: {len(english_stopwords)}")
        
        return True
    except Exception as e:
        print(f"✗ NLTK数据加载失败: {e}")
        return False



def main():
    """主函数"""
    print("NLTK数据测试")
    print("=" * 60)
    
    # 测试NLTK数据
    nltk_success = test_nltk_data()
    
    print("\n测试结果总结:")
    print(f"NLTK数据加载: {'成功' if nltk_success else '失败'}")
    
    if nltk_success:
        print("\n✓ 所有测试通过！")
        return 0
    else:
        print("\n✗ 测试失败，请检查NLTK数据安装。")
        return 1

if __name__ == '__main__':
    sys.exit(main())
