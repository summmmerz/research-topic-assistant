#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动下载NLTK数据

直接从GitHub下载NLTK数据文件并解压到指定目录
"""

import os
import sys
import urllib.request
import zipfile

# 设置NLTK数据目录
NLTK_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'nltk_data')

# 确保目录存在
os.makedirs(NLTK_DATA_DIR, exist_ok=True)

# 数据文件URL和目标目录
DATA_FILES = [
    {
        'url': 'https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt.zip',
        'target_dir': os.path.join(NLTK_DATA_DIR, 'tokenizers'),
        'name': 'punkt'
    },
    {
        'url': 'https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/stopwords.zip',
        'target_dir': os.path.join(NLTK_DATA_DIR, 'corpora'),
        'name': 'stopwords'
    }
]

def download_file(url, target_path):
    """下载文件"""
    print(f"下载 {url} 到 {target_path}...")
    try:
        urllib.request.urlretrieve(url, target_path)
        print(f"✓ 下载成功")
        return True
    except Exception as e:
        print(f"✗ 下载失败: {e}")
        return False

def unzip_file(zip_path, extract_dir):
    """解压文件"""
    print(f"解压 {zip_path} 到 {extract_dir}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print(f"✓ 解压成功")
        return True
    except Exception as e:
        print(f"✗ 解压失败: {e}")
        return False

def main():
    """主函数"""
    print("手动下载NLTK数据")
    print("=" * 50)
    print(f"NLTK数据目录: {NLTK_DATA_DIR}")
    
    all_success = True
    
    for data_file in DATA_FILES:
        print(f"\n处理 {data_file['name']} 数据...")
        
        # 确保目标目录存在
        os.makedirs(data_file['target_dir'], exist_ok=True)
        
        # 下载文件
        zip_path = os.path.join(data_file['target_dir'], f"{data_file['name']}.zip")
        if not download_file(data_file['url'], zip_path):
            all_success = False
            continue
        
        # 解压文件
        if not unzip_file(zip_path, data_file['target_dir']):
            all_success = False
            continue
        
        # 删除zip文件
        try:
            os.remove(zip_path)
            print(f"✓ 已删除临时zip文件")
        except Exception as e:
            print(f"✗ 删除临时文件失败: {e}")
    
    print("\n" + "=" * 50)
    if all_success:
        print("✓ 所有NLTK数据下载成功！")
        print(f"数据已安装到: {NLTK_DATA_DIR}")
    else:
        print("✗ 部分数据下载失败，请检查网络连接。")

if __name__ == '__main__':
    main()
