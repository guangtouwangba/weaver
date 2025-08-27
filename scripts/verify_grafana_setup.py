#!/usr/bin/env python3
"""
验证Grafana + Elasticsearch设置是否正常工作
"""

import requests
import json
import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

GRAFANA_URL = "http://localhost:3000"
GRAFANA_AUTH = ("admin", "admin123")

def check_services():
    """检查基础服务状态"""
    print("🔍 检查基础服务...")
    
    services = {
        "Grafana": "http://localhost:3000/api/health",
        "Elasticsearch": "http://localhost:9200/_cluster/health"
    }
    
    all_ok = True
    for name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {name}: 运行正常")
            else:
                print(f"  ❌ {name}: 状态码 {response.status_code}")
                all_ok = False
        except Exception as e:
            print(f"  ❌ {name}: 连接失败 - {e}")
            all_ok = False
    
    return all_ok

def check_elasticsearch_data():
    """检查Elasticsearch中的数据"""
    print("\n📊 检查Elasticsearch数据...")
    
    try:
        response = requests.get("http://localhost:9200/chat-*/_count")
        if response.status_code == 200:
            data = response.json()
            count = data.get("count", 0)
            print(f"  📈 总消息数: {count}")
            
            if count == 0:
                print("  ⚠️  没有数据，正在添加测试数据...")
                add_test_data()
                return True
            else:
                return True
        else:
            print(f"  ❌ 查询失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ 查询出错: {e}")
        return False

def add_test_data():
    """添加测试数据"""
    async def _add_data():
        try:
            from modules.services.elasticsearch_service import elasticsearch_chat_service
            
            await elasticsearch_chat_service.initialize()
            
            test_conversations = [
                ("verification-001", "验证测试消息1", "这是验证回复1"),
                ("verification-002", "验证测试消息2", "这是验证回复2"),
                ("verification-003", "Grafana可视化测试", "现在你可以在Grafana中看到这条消息了！")
            ]
            
            for conv_id, user_msg, assistant_msg in test_conversations:
                result = await elasticsearch_chat_service.save_conversation(
                    conversation_id=conv_id,
                    user_message=user_msg,
                    assistant_message=assistant_msg,
                    ai_metadata={"verification": True, "timestamp": "2025-08-27"}
                )
                if result:
                    print(f"    ✅ 添加对话: {conv_id}")
            
            await elasticsearch_chat_service.close()
            print("  ✅ 测试数据添加完成")
            
        except Exception as e:
            print(f"  ❌ 添加测试数据失败: {e}")
    
    asyncio.run(_add_data())

def check_grafana_datasource():
    """检查Grafana数据源"""
    print("\n🔌 检查Grafana数据源...")
    
    try:
        response = requests.get(f"{GRAFANA_URL}/api/datasources", auth=GRAFANA_AUTH)
        if response.status_code == 200:
            datasources = response.json()
            es_datasources = [ds for ds in datasources if ds.get("type") == "elasticsearch"]
            
            if not es_datasources:
                print("  ❌ 没有找到Elasticsearch数据源")
                return False
            
            for ds in es_datasources:
                print(f"  ✅ 数据源: {ds.get('name')} (ID: {ds.get('id')})")
                print(f"     URL: {ds.get('url')}")
                print(f"     Database: {ds.get('database')}")
                
                # 测试连接
                test_url = f"{GRAFANA_URL}/api/datasources/proxy/{ds.get('id')}/_cluster/health"
                test_response = requests.get(test_url, auth=GRAFANA_AUTH, timeout=10)
                
                if test_response.status_code == 200:
                    health = test_response.json()
                    print(f"     状态: ✅ {health.get('status', 'unknown')}")
                else:
                    print(f"     状态: ⚠️  HTTP {test_response.status_code}")
            
            return True
        else:
            print(f"  ❌ 无法获取数据源列表: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ 检查数据源失败: {e}")
        return False

def check_dashboard():
    """检查Dashboard"""
    print("\n📊 检查Dashboard...")
    
    try:
        response = requests.get(f"{GRAFANA_URL}/api/search", auth=GRAFANA_AUTH)
        if response.status_code == 200:
            dashboards = response.json()
            chat_dashboards = [db for db in dashboards if "chat" in db.get("title", "").lower()]
            
            if not chat_dashboards:
                print("  ❌ 没有找到聊天相关的Dashboard")
                return False
            
            for db in chat_dashboards:
                print(f"  ✅ Dashboard: {db.get('title')}")
                print(f"     URL: {GRAFANA_URL}{db.get('url')}")
            
            return True
        else:
            print(f"  ❌ 无法获取Dashboard列表: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ 检查Dashboard失败: {e}")
        return False

def main():
    """主验证流程"""
    print("🚀 验证Grafana + Elasticsearch设置")
    print("=" * 50)
    
    success = True
    
    # 检查基础服务
    if not check_services():
        success = False
    
    # 检查数据
    if not check_elasticsearch_data():
        success = False
    
    # 检查数据源
    if not check_grafana_datasource():
        success = False
    
    # 检查Dashboard
    if not check_dashboard():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 验证完成！所有组件都工作正常")
        print()
        print("🌐 访问信息:")
        print(f"   Grafana: {GRAFANA_URL}")
        print("   用户名: admin / 密码: admin123")
        print()
        print("📊 快速访问:")
        print("   make grafana-open        # 打开Grafana")
        print("   make grafana-dashboard   # 打开聊天Dashboard")
        print("   make grafana-status      # 查看数据源状态")
        print()
        print("🎉 现在你可以在Grafana中查看Elasticsearch数据了！")
    else:
        print("❌ 验证失败，请检查上述错误")
        print()
        print("🔧 修复建议:")
        print("   make grafana-fix         # 修复数据源问题")
        print("   make start              # 重启所有服务")
        print("   make grafana-test-data   # 添加测试数据")

if __name__ == "__main__":
    main()