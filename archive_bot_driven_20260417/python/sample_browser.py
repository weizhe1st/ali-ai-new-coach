#!/usr/bin/env python3
"""
样本检索和访问页面（命令行版本）
提供统一的样本检索和访问接口
"""

import os
import sys
import json
from datetime import datetime
from sample_index_service import SampleIndexService

def display_sample_list(samples: list, index_service: SampleIndexService):
    """显示样本列表"""
    if not samples:
        print("   没有找到符合条件的样本")
        return
    
    print(f"\n   找到 {len(samples)} 个样本:\n")
    print(f"   {'Sample ID':<30} {'NTRP':<6} {'分类':<18} {'状态':<10}")
    print(f"   {'-'*30} {'-'*6} {'-'*18} {'-'*10}")
    
    for sample in samples[:20]:  # 最多显示 20 个
        sample_id = sample.get('sample_id', 'N/A')[:29]
        ntrp = sample.get('ntrp_level', 'N/A')
        category = sample.get('sample_category', 'unknown')
        status = index_service._get_sample_status(sample)
        
        print(f"   {sample_id:<30} {ntrp:<6} {category:<18} {status:<10}")
    
    if len(samples) > 20:
        print(f"\n   ... 还有 {len(samples) - 20} 个样本，请使用更精确的搜索条件")

def display_sample_detail(sample_id: str, index_service: SampleIndexService):
    """显示样本详情"""
    display_info = index_service.get_sample_display_info(sample_id)
    
    if 'error' in display_info:
        print(f"\n   ❌ {display_info['error']}")
        return
    
    print("\n" + "="*60)
    print(f"📹 样本详情：{sample_id}")
    print("="*60)
    print()
    print(f"   Sample ID: {display_info['sample_id']}")
    print(f"   NTRP 等级：{display_info['ntrp_level']}")
    print(f"   分类：{display_info['category']}")
    print(f"   主要问题：{display_info['primary_issue'] or '无'}")
    print(f"   次要问题：{display_info['secondary_issue'] or '无'}")
    print()
    
    # 视频访问信息
    video_info = display_info['video_info']
    print(f"📋 视频访问信息:")
    print(f"   状态：{video_info['status']}")
    print(f"   访问方式：{video_info['access_type']}")
    print(f"   说明：{video_info['message']}")
    
    if video_info.get('url'):
        print(f"   URL: {video_info['url'][:80]}...")
    if video_info.get('local_path'):
        print(f"   本地路径：{video_info['local_path']}")
    
    print()
    print(f"样本状态：{display_info['status']}")
    print()

def main():
    """主函数"""
    print("="*60)
    print("📚 样本统一检索和访问系统")
    print("="*60)
    print()
    
    # 创建索引服务
    index_service = SampleIndexService()
    
    while True:
        print("\n请选择操作:")
        print("   1. 搜索样本")
        print("   2. 查看样本详情")
        print("   3. 查看统计信息")
        print("   4. 退出")
        print()
        
        choice = input("   输入选项 (1-4): ").strip()
        
        if choice == '1':
            # 搜索样本
            print("\n🔍 搜索样本")
            print()
            
            ntrp = input("   NTRP 等级（留空跳过）: ").strip() or None
            category = input("   分类（excellent_demo/typical_issue，留空跳过）: ").strip() or None
            issue = input("   主要问题（留空跳过）: ").strip() or None
            has_cos = input("   是否已上传 COS（y/n，留空跳过）: ").strip()
            
            if has_cos == 'y':
                has_cos_url = True
            elif has_cos == 'n':
                has_cos_url = False
            else:
                has_cos_url = None
            
            samples = index_service.search_samples(
                ntrp_level=ntrp,
                category=category,
                primary_issue=issue,
                has_cos_url=has_cos_url
            )
            
            display_sample_list(samples, index_service)
        
        elif choice == '2':
            # 查看样本详情
            print("\n📹 查看样本详情")
            print()
            
            sample_id = input("   输入 Sample ID: ").strip()
            display_sample_detail(sample_id, index_service)
        
        elif choice == '3':
            # 查看统计信息
            print()
            print(index_service.export_index_summary())
        
        elif choice == '4':
            print("\n👋 再见！")
            break
        
        else:
            print("\n   ❌ 无效选项，请重新输入")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 再见！")
        sys.exit(0)
