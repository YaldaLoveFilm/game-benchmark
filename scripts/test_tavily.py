#!/usr/bin/env python3
"""
测试Tavily深度搜索 - 新的核心数据源
"""

import os
import json
import sys

def test_tavily_search(game_name):
    """测试Tavily搜索能力"""
    print(f"🔍 测试Tavily搜索: {game_name}")
    
    # 尝试导入tavily
    try:
        from tavily import TavilyClient
    except ImportError:
        print("❌ 需要安装tavily库: pip install tavily-python")
        return None
    
    # 获取API key
    api_key = os.getenv('TAVILY_API_KEY')
    if not api_key:
        print("❌ TAVILY_API_KEY环境变量未设置")
        return None
    
    try:
        client = TavilyClient(api_key=api_key)
        
        # 构建搜索查询
        queries = [
            f"{game_name} Android iOS 下载量 评分 2026",
            f"{game_name} 官方 Twitter TikTok 粉丝数",
            f"{game_name} YouTube 创作者 直播 视频",
            f"{game_name} 用户评价 评论 优缺点"
        ]
        
        all_results = []
        
        for query in queries:
            print(f"\n📝 搜索: {query}")
            try:
                response = client.search(
                    query=query,
                    search_depth='advanced',
                    max_results=5
                )
                
                if 'results' in response:
                    for result in response['results']:
                        # 提取关键信息
                        item = {
                            'title': result.get('title', ''),
                            'url': result.get('url', ''),
                            'content': result.get('content', '')[:200] + '...' if result.get('content') else '',
                            'score': result.get('score', 0)
                        }
                        all_results.append(item)
                        print(f"  • {item['title']}")
                        print(f"    {item['url']}")
                
            except Exception as e:
                print(f"  ⚠️ 搜索失败: {e}")
                continue
        
        return all_results
        
    except Exception as e:
        print(f"❌ Tavily搜索错误: {e}")
        return None

def analyze_game_data(game_name, results):
    """分析游戏数据"""
    print(f"\n📊 数据分析: {game_name}")
    
    if not results:
        print("❌ 无搜索结果")
        return
    
    # 分类统计
    categories = {
        'platform_data': 0,  # 平台数据
        'social_media': 0,   # 社交媒体
        'creators': 0,       # 创作者
        'reviews': 0,        # 评价
        'news': 0            # 新闻
    }
    
    keywords = {
        'platform_data': ['下载量', '评分', '安装', '收入', 'DAU', 'MAU'],
        'social_media': ['Twitter', 'TikTok', '抖音', 'Facebook', 'Instagram', '粉丝'],
        'creators': ['YouTube', '直播', '创作者', '主播', '视频'],
        'reviews': ['评价', '评论', '优缺点', '用户反馈', '评分'],
        'news': ['新闻', '报道', '更新', '版本', '活动']
    }
    
    for result in results:
        title = result['title'].lower()
        content = result['content'].lower()
        
        for category, kw_list in keywords.items():
            for kw in kw_list:
                if kw.lower() in title or kw.lower() in content:
                    categories[category] += 1
                    break
    
    print("📈 数据分布:")
    for category, count in categories.items():
        print(f"  {category}: {count}条")
    
    # 提取关键信息
    print("\n🔑 关键发现:")
    
    # 平台数据
    platform_results = [r for r in results if any(kw in r['title'] for kw in keywords['platform_data'])]
    if platform_results:
        print("  • 平台数据:")
        for r in platform_results[:2]:
            print(f"    - {r['title']}")
    
    # 社交媒体
    social_results = [r for r in results if any(kw in r['title'] for kw in keywords['social_media'])]
    if social_results:
        print("  • 社交媒体:")
        for r in social_results[:2]:
            print(f"    - {r['title']}")
    
    # 创作者
    creator_results = [r for r in results if any(kw in r['title'] for kw in keywords['creators'])]
    if creator_results:
        print("  • 创作者生态:")
        for r in creator_results[:2]:
            print(f"    - {r['title']}")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python test_tavily.py <游戏名称>")
        sys.exit(1)
    
    game_name = sys.argv[1]
    
    print(f"🎮 开始分析: {game_name}")
    print("=" * 50)
    
    # 测试Tavily搜索
    results = test_tavily_search(game_name)
    
    if results:
        print(f"\n✅ 搜索完成，共找到 {len(results)} 条结果")
        
        # 分析数据
        analyze_game_data(game_name, results)
        
        # 保存结果
        output_file = f"{game_name}_tavily_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 结果已保存到: {output_file}")
    else:
        print("❌ 搜索失败")

if __name__ == "__main__":
    main()