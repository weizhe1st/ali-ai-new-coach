#!/usr/bin/env python3
"""
样本审核命令行工具

支持的操作：
- show: 查看单个样本
- list: 列出样本（支持过滤）
- approve: 审核通过
- reject: 审核拒绝
- set-category: 设置分类
- set-ntrp: 设置 NTRP 等级
- add-tags: 添加标签
- remove-tags: 移除标签
- summary: 统计摘要
"""

import os
import sys
import argparse
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from sample_review_service import SampleReviewService


def format_sample_display(record: dict) -> str:
    """格式化样本显示"""
    lines = []
    lines.append("="*60)
    lines.append(f"📋 样本信息：{record.get('sample_id', 'N/A')}")
    lines.append("="*60)
    
    # 基本信息
    lines.append(f"\n📝 基本信息:")
    lines.append(f"   样本 ID: {record.get('sample_id', 'N/A')}")
    lines.append(f"   来源类型：{record.get('source_type', 'N/A')}")
    lines.append(f"   动作类型：{record.get('action_type', 'N/A')}")
    lines.append(f"   样本分类：{record.get('sample_category', 'unknown')}")
    lines.append(f"   文件名：{record.get('source_file_name', 'N/A')}")
    
    # COS 信息
    lines.append(f"\n📦 COS 信息:")
    lines.append(f"   COS Key: {record.get('cos_key', 'N/A')}")
    cos_url = record.get('cos_url', '')
    if cos_url:
        lines.append(f"   COS URL: {cos_url[:80]}...")
    
    # 审核状态
    lines.append(f"\n🔍 审核状态:")
    lines.append(f"   审核状态：{record.get('golden_review_status', 'N/A')}")
    lines.append(f"   审核人：{record.get('reviewer', 'N/A')}")
    lines.append(f"   审核时间：{record.get('reviewed_at', 'N/A')}")
    if record.get('golden_review_note'):
        lines.append(f"   审核备注：{record.get('golden_review_note')}")
    
    # 分析信息
    lines.append(f"\n📊 分析信息:")
    analysis = record.get('analysis_summary', {})
    if analysis:
        lines.append(f"   NTRP 等级：{analysis.get('ntrp_level', record.get('ntrp_level', 'N/A'))}")
        lines.append(f"   整体评分：{analysis.get('overall_score', 'N/A')}")
    else:
        lines.append(f"   NTRP 等级：{record.get('ntrp_level', 'N/A')}")
    
    # 标签
    tags = record.get('tags', [])
    if tags:
        lines.append(f"   标签：{', '.join(tags)}")
    else:
        lines.append(f"   标签：无")
    
    # 时间信息
    lines.append(f"\n⏰ 时间信息:")
    lines.append(f"   导入时间：{record.get('imported_at', 'N/A')}")
    if record.get('last_modified'):
        lines.append(f"   最后修改：{record.get('last_modified')}")
    
    lines.append("\n" + "="*60)
    
    return "\n".join(lines)


def cmd_show(args):
    """查看单个样本"""
    service = SampleReviewService()
    
    record = service.get_sample(args.sample_id)
    
    if not record:
        print(f"❌ 样本不存在：{args.sample_id}")
        return 1
    
    print(format_sample_display(record))
    return 0


def cmd_list(args):
    """列出样本"""
    service = SampleReviewService()
    
    records = service.list_samples(
        status=args.status,
        action_type=args.action_type,
        limit=args.limit
    )
    
    if not records:
        print("没有找到符合条件的样本")
        return 0
    
    print(f"\n找到 {len(records)} 个样本:\n")
    
    # 表头
    print(f"{'sample_id':<25} {'action_type':<15} {'status':<18} {'category':<15} {'filename':<30}")
    print("-"*103)
    
    # 数据行
    for record in records:
        sample_id = record.get('sample_id', 'N/A')[:24]
        action = record.get('action_type', 'N/A')[:14]
        status = record.get('golden_review_status', 'N/A')[:17]
        category = record.get('sample_category', 'unknown')[:14]
        filename = record.get('source_file_name', 'N/A')[:29]
        
        print(f"{sample_id:<25} {action:<15} {status:<18} {category:<15} {filename:<30}")
    
    print(f"\n总计：{len(records)} 个样本")
    
    if args.status:
        print(f"过滤条件：status={args.status}")
    if args.action_type:
        print(f"过滤条件：action_type={args.action_type}")
    if args.limit and len(records) == args.limit:
        print(f"数量限制：{args.limit}")
    
    print()
    return 0


def cmd_approve(args):
    """审核通过"""
    service = SampleReviewService()
    
    result = service.approve_sample(
        sample_id=args.sample_id,
        reviewer=args.reviewer,
        note=args.note
    )
    
    if result.get('success'):
        print("\n✅ 审核通过")
        print(f"   sample_id: {result['sample_id']}")
        print(f"   review_status: {result['review_status']}")
        print(f"   reviewer: {result['reviewer']}")
        print(f"   reviewed_at: {result['reviewed_at']}")
        print(f"   note: {result['note']}")
        print()
        return 0
    else:
        print(f"\n❌ 审核失败：{result.get('error')}")
        return 1


def cmd_reject(args):
    """审核拒绝"""
    service = SampleReviewService()
    
    result = service.reject_sample(
        sample_id=args.sample_id,
        reviewer=args.reviewer,
        note=args.note
    )
    
    if result.get('success'):
        print("\n✅ 审核拒绝")
        print(f"   sample_id: {result['sample_id']}")
        print(f"   review_status: {result['review_status']}")
        print(f"   reviewer: {result['reviewer']}")
        print(f"   reviewed_at: {result['reviewed_at']}")
        print(f"   note: {result['note']}")
        print()
        return 0
    else:
        print(f"\n❌ 审核失败：{result.get('error')}")
        return 1


def cmd_set_category(args):
    """设置分类"""
    service = SampleReviewService()
    
    result = service.set_category(
        sample_id=args.sample_id,
        category=args.category
    )
    
    if result.get('success'):
        print("\n✅ 分类已更新")
        print(f"   sample_id: {result['sample_id']}")
        print(f"   sample_category: {result['sample_category']}")
        print()
        return 0
    else:
        print(f"\n❌ 更新失败：{result.get('error')}")
        if result.get('valid_categories'):
            print(f"   有效分类：{', '.join(result['valid_categories'])}")
        return 1


def cmd_set_ntrp(args):
    """设置 NTRP 等级"""
    service = SampleReviewService()
    
    result = service.set_ntrp(
        sample_id=args.sample_id,
        ntrp_level=args.ntrp
    )
    
    if result.get('success'):
        print("\n✅ NTRP 等级已更新")
        print(f"   sample_id: {result['sample_id']}")
        print(f"   ntrp_level: {result['ntrp_level'] if result['ntrp_level'] else '已清除'}")
        print()
        return 0
    else:
        print(f"\n❌ 更新失败：{result.get('error')}")
        if result.get('valid_levels'):
            print(f"   有效等级：{', '.join(result['valid_levels'])}")
        return 1


def cmd_add_tags(args):
    """添加标签"""
    service = SampleReviewService()
    
    # 解析标签（逗号分隔）
    tags = [t.strip() for t in args.tags.split(',') if t.strip()]
    
    result = service.add_tags(
        sample_id=args.sample_id,
        tags=tags
    )
    
    if result.get('success'):
        print("\n✅ 标签已添加")
        print(f"   sample_id: {result['sample_id']}")
        print(f"   tags: {', '.join(result['tags'])}")
        print()
        return 0
    else:
        print(f"\n❌ 更新失败：{result.get('error')}")
        return 1


def cmd_remove_tags(args):
    """移除标签"""
    service = SampleReviewService()
    
    # 解析标签（逗号分隔）
    tags = [t.strip() for t in args.tags.split(',') if t.strip()]
    
    result = service.remove_tags(
        sample_id=args.sample_id,
        tags=tags
    )
    
    if result.get('success'):
        print("\n✅ 标签已移除")
        print(f"   sample_id: {result['sample_id']}")
        if result['tags']:
            print(f"   剩余 tags: {', '.join(result['tags'])}")
        else:
            print(f"   剩余 tags: 无")
        print()
        return 0
    else:
        print(f"\n❌ 更新失败：{result.get('error')}")
        return 1


def cmd_summary(args):
    """统计摘要"""
    service = SampleReviewService()
    
    summary = service.get_summary()
    
    print("\n" + "="*60)
    print("📊 样本统计摘要")
    print("="*60)
    
    print(f"\n📈 总样本数：{summary.get('total', 0)}")
    
    print(f"\n📁 按来源分类:")
    for source, count in summary.get('by_source', {}).items():
        print(f"   {source}: {count}")
    
    print(f"\n🎯 按动作类型分类:")
    for action, count in summary.get('by_action', {}).items():
        print(f"   {action}: {count}")
    
    print(f"\n🔍 按审核状态分类:")
    for status, count in summary.get('by_status', {}).items():
        print(f"   {status}: {count}")
    
    print(f"\n📋 按样本分类:")
    for category, count in summary.get('by_category', {}).items():
        print(f"   {category}: {count}")
    
    print("\n" + "="*60 + "\n")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='样本审核命令行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s show --sample-id legacy_0001
  %(prog)s list --status pending
  %(prog)s approve --sample-id candidate_0001 --reviewer weizhe --note "动作完整"
  %(prog)s reject --sample-id candidate_0002 --reviewer weizhe --note "遮挡严重"
  %(prog)s set-category --sample-id legacy_0001 --category excellent_demo
  %(prog)s set-ntrp --sample-id legacy_0001 --ntrp 3.5
  %(prog)s add-tags --sample-id legacy_0001 --tags toss,timing,loading
  %(prog)s summary
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # show 命令
    show_parser = subparsers.add_parser('show', help='查看单个样本')
    show_parser.add_argument('--sample-id', required=True, help='样本 ID')
    show_parser.set_defaults(func=cmd_show)
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='列出样本')
    list_parser.add_argument('--status', help='审核状态过滤')
    list_parser.add_argument('--action-type', help='动作类型过滤')
    list_parser.add_argument('--limit', type=int, default=0, help='数量限制')
    list_parser.set_defaults(func=cmd_list)
    
    # approve 命令
    approve_parser = subparsers.add_parser('approve', help='审核通过')
    approve_parser.add_argument('--sample-id', required=True, help='样本 ID')
    approve_parser.add_argument('--reviewer', required=True, help='审核人')
    approve_parser.add_argument('--note', default='', help='审核备注')
    approve_parser.set_defaults(func=cmd_approve)
    
    # reject 命令
    reject_parser = subparsers.add_parser('reject', help='审核拒绝')
    reject_parser.add_argument('--sample-id', required=True, help='样本 ID')
    reject_parser.add_argument('--reviewer', required=True, help='审核人')
    reject_parser.add_argument('--note', default='', help='审核备注')
    reject_parser.set_defaults(func=cmd_reject)
    
    # set-category 命令
    category_parser = subparsers.add_parser('set-category', help='设置样本分类')
    category_parser.add_argument('--sample-id', required=True, help='样本 ID')
    category_parser.add_argument('--category', required=True, help='分类')
    category_parser.set_defaults(func=cmd_set_category)
    
    # set-ntrp 命令
    ntrp_parser = subparsers.add_parser('set-ntrp', help='设置 NTRP 等级')
    ntrp_parser.add_argument('--sample-id', required=True, help='样本 ID')
    ntrp_parser.add_argument('--ntrp', required=True, help='NTRP 等级')
    ntrp_parser.set_defaults(func=cmd_set_ntrp)
    
    # add-tags 命令
    add_tags_parser = subparsers.add_parser('add-tags', help='添加标签')
    add_tags_parser.add_argument('--sample-id', required=True, help='样本 ID')
    add_tags_parser.add_argument('--tags', required=True, help='标签（逗号分隔）')
    add_tags_parser.set_defaults(func=cmd_add_tags)
    
    # remove-tags 命令
    remove_tags_parser = subparsers.add_parser('remove-tags', help='移除标签')
    remove_tags_parser.add_argument('--sample-id', required=True, help='样本 ID')
    remove_tags_parser.add_argument('--tags', required=True, help='标签（逗号分隔）')
    remove_tags_parser.set_defaults(func=cmd_remove_tags)
    
    # summary 命令
    summary_parser = subparsers.add_parser('summary', help='统计摘要')
    summary_parser.set_defaults(func=cmd_summary)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
