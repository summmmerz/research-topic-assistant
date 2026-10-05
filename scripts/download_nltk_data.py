#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NLTK数据下载脚本

用于手动下载NLTK所需的数据
"""

import nltk
import os
import sys
import urllib.request
import zipfile
import shutil

# 设置NLTK数据目录
NLTK_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'nltk_data')

# 确保目录存在
os.makedirs(NLTK_DATA_DIR, exist_ok=True)

# 设置NLTK数据路径
os.environ['NLTK_DATA'] = NLTK_DATA_DIR
print(f"NLTK数据目录: {NLTK_DATA_DIR}")

# 尝试自动下载
def try_auto_download():
    """尝试自动下载NLTK数据"""
    print("\n尝试自动下载NLTK数据...")
    try:
        nltk.download('punkt', download_dir=NLTK_DATA_DIR)
        nltk.download('stopwords', download_dir=NLTK_DATA_DIR)
        print("自动下载成功！")
        return True
    except Exception as e:
        print(f"自动下载失败: {e}")
        return False

# 手动下载函数
def manual_download():
    """手动下载NLTK数据"""
    print("\n开始手动下载NLTK数据...")
    
    # 数据文件URL
    punkt_url = "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt.zip"
    stopwords_url = "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/stopwords.zip"
    
    # 下载目录
    tokenizers_dir = os.path.join(NLTK_DATA_DIR, 'tokenizers')
    corpora_dir = os.path.join(NLTK_DATA_DIR, 'corpora')
    
    # 确保目录存在
    os.makedirs(tokenizers_dir, exist_ok=True)
    os.makedirs(corpora_dir, exist_ok=True)
    
    # 下载punkt
    print("下载punkt数据...")
    try:
        urllib.request.urlretrieve(punkt_url, os.path.join(tokenizers_dir, 'punkt.zip'))
        with zipfile.ZipFile(os.path.join(tokenizers_dir, 'punkt.zip'), 'r') as zip_ref:
            zip_ref.extractall(tokenizers_dir)
        os.remove(os.path.join(tokenizers_dir, 'punkt.zip'))
        print("punkt数据下载成功！")
    except Exception as e:
        print(f"punkt数据下载失败: {e}")
        return False
    
    # 下载stopwords
    print("下载stopwords数据...")
    try:
        urllib.request.urlretrieve(stopwords_url, os.path.join(corpora_dir, 'stopwords.zip'))
        with zipfile.ZipFile(os.path.join(corpora_dir, 'stopwords.zip'), 'r') as zip_ref:
            zip_ref.extractall(corpora_dir)
        os.remove(os.path.join(corpora_dir, 'stopwords.zip'))
        print("stopwords数据下载成功！")
    except Exception as e:
        print(f"stopwords数据下载失败: {e}")
        return False
    
    return True

# 验证数据是否安装成功
def verify_installation():
    """验证NLTK数据是否安装成功"""
    print("\n验证NLTK数据安装...")
    try:
        from nltk.tokenize import word_tokenize
        from nltk.corpus import stopwords
        
        # 测试tokenize
        test_text = "Hello, world! This is a test."
        tokens = word_tokenize(test_text)
        print(f"Tokenize测试成功: {tokens}")
        
        # 测试stopwords
        english_stopwords = stopwords.words('english')
        print(f"Stopwords测试成功，英语停用词数量: {len(english_stopwords)}")
        
        return True
    except Exception as e:
        print(f"验证失败: {e}")
        return False

# 主函数
def main():
    """主函数"""
    print("NLTK数据下载工具")
    print("=" * 50)
    
    # 首先尝试自动下载
    if try_auto_download():
        if verify_installation():
            print("\nNLTK数据安装成功！")
            return
    
    # 如果自动下载失败，尝试手动下载
    print("\n自动下载失败，尝试手动下载...")
    if manual_download():
        if verify_installation():
            print("\nNLTK数据安装成功！")
            return
    
    print("\nNLTK数据安装失败，请检查网络连接或手动下载数据。")
    print("\n手动下载步骤:")
    print("1. 访问 https://github.com/nltk/nltk_data/tree/gh-pages/packages")
    print("2. 下载 tokenizers/punkt.zip 和 corpora/stopwords.zip")
    print(f"3. 解压到 {NLTK_DATA_DIR} 目录下")
    print("4. 确保目录结构为:")
    print(f"   {NLTK_DATA_DIR}/tokenizers/punkt/")
    print(f"   {NLTK_DATA_DIR}/corpora/stopwords/")

if __name__ == '__main__':
    main()
