#!/usr/bin/env python3
"""
设置Grafana Elasticsearch数据源和Dashboard的工具脚本
"""

import asyncio
import requests
import json
import time
from typing import Dict, Any

# Grafana配置
GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "admin123"
GRAFANA_AUTH = (GRAFANA_USER, GRAFANA_PASSWORD)

# Elasticsearch配置
ES_URL = "http://elasticsearch:9200"

def check_grafana_ready():
    """检查Grafana是否准备就绪"""
    try:
        response = requests.get(f"{GRAFANA_URL}/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def create_elasticsearch_datasource():
    """创建Elasticsearch数据源"""
    datasource_config = {
        "name": "elasticsearch-chat-manual",
        "type": "elasticsearch",
        "url": ES_URL,
        "access": "proxy",
        "database": "chat-messages-*",
        "basicAuth": False,
        "isDefault": False,
        "jsonData": {
            "interval": "Daily",
            "timeField": "timestamp",
            "esVersion": "8.0.0",
            "maxConcurrentShardRequests": 5,
            "logMessageField": "user_message",
            "includeFrozen": False
        }
    }
    
    try:
        # 首先检查数据源是否已存在
        response = requests.get(
            f"{GRAFANA_URL}/api/datasources/name/{datasource_config['name']}", 
            auth=GRAFANA_AUTH
        )
        
        if response.status_code == 200:
            print(f"✅ 数据源 '{datasource_config['name']}' 已存在")
            return response.json()
        
        # 创建新数据源
        response = requests.post(
            f"{GRAFANA_URL}/api/datasources",
            auth=GRAFANA_AUTH,
            json=datasource_config,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功创建数据源: {result.get('name')} (ID: {result.get('id')})")
            return result
        else:
            print(f"❌ 创建数据源失败: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 创建数据源时出错: {e}")
        return None

def test_datasource(datasource_id):
    """测试数据源连接"""
    try:
        response = requests.post(
            f"{GRAFANA_URL}/api/datasources/{datasource_id}/proxy/_search?size=1",
            auth=GRAFANA_AUTH,
            json={"query": {"match_all": {}}},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            total = result.get("hits", {}).get("total", {}).get("value", 0)
            print(f"✅ 数据源连接测试成功，找到 {total} 条记录")
            return True
        else:
            print(f"❌ 数据源连接测试失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试数据源时出错: {e}")
        return False

def create_simple_dashboard(datasource_uid):
    """创建简单的聊天Dashboard"""
    dashboard_config = {
        "dashboard": {
            "id": None,
            "title": "Chat Messages Dashboard",
            "tags": ["elasticsearch", "chat"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "Total Messages",
                    "type": "stat",
                    "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "datasource": {"uid": datasource_uid},
                            "query": "*",
                            "metrics": [{"id": "1", "type": "count"}],
                            "bucketAggs": [],
                            "timeField": "timestamp"
                        }
                    ]
                },
                {
                    "id": 2,
                    "title": "Messages Over Time",
                    "type": "timeseries", 
                    "gridPos": {"h": 8, "w": 18, "x": 6, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "datasource": {"uid": datasource_uid},
                            "query": "*",
                            "metrics": [{"id": "1", "type": "count"}],
                            "bucketAggs": [
                                {
                                    "id": "2",
                                    "type": "date_histogram",
                                    "field": "timestamp",
                                    "settings": {"interval": "1h"}
                                }
                            ],
                            "timeField": "timestamp"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "custom": {
                                "drawStyle": "line",
                                "lineInterpolation": "linear",
                                "barAlignment": 0,
                                "lineWidth": 1,
                                "fillOpacity": 10,
                                "gradientMode": "none",
                                "spanNulls": False,
                                "insertNulls": False,
                                "showPoints": "never",
                                "pointSize": 5
                            }
                        }
                    }
                },
                {
                    "id": 3,
                    "title": "Recent Messages",
                    "type": "table",
                    "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8},
                    "targets": [
                        {
                            "refId": "A", 
                            "datasource": {"uid": datasource_uid},
                            "query": "*",
                            "metrics": [{"id": "1", "type": "raw_data", "settings": {"size": 10}}],
                            "bucketAggs": [],
                            "timeField": "timestamp"
                        }
                    ]
                }
            ],
            "time": {"from": "now-24h", "to": "now"},
            "refresh": "30s"
        },
        "overwrite": True
    }
    
    try:
        response = requests.post(
            f"{GRAFANA_URL}/api/dashboards/db",
            auth=GRAFANA_AUTH,
            json=dashboard_config,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功创建Dashboard: {result.get('title')}")
            print(f"   访问链接: {GRAFANA_URL}{result.get('url')}")
            return result
        else:
            print(f"❌ 创建Dashboard失败: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 创建Dashboard时出错: {e}")
        return None

def main():
    """主函数"""
    print("🚀 开始设置Grafana Elasticsearch集成...")
    print()
    
    # 等待Grafana启动
    print("⏳ 等待Grafana启动...")
    max_retries = 30
    for i in range(max_retries):
        if check_grafana_ready():
            print("✅ Grafana已准备就绪")
            break
        time.sleep(2)
        print(f"   等待中... ({i+1}/{max_retries})")
    else:
        print("❌ Grafana启动超时")
        return
    
    print()
    
    # 创建数据源
    print("📊 创建Elasticsearch数据源...")
    datasource = create_elasticsearch_datasource()
    if not datasource:
        return
    
    print()
    
    # 测试数据源
    print("🔍 测试数据源连接...")
    if not test_datasource(datasource.get("id")):
        print("⚠️  数据源连接有问题，但会继续创建Dashboard")
    
    print()
    
    # 创建Dashboard
    print("📋 创建简单Dashboard...")
    dashboard = create_simple_dashboard(datasource.get("uid"))
    
    print()
    print("✨ 设置完成！")
    print()
    print("🌐 访问信息:")
    print(f"   Grafana: {GRAFANA_URL}")
    print(f"   用户名: {GRAFANA_USER}")
    print(f"   密码: {GRAFANA_PASSWORD}")
    print()
    print("💡 使用说明:")
    print("   1. 访问Grafana并登录")
    print("   2. 在左侧菜单选择 'Dashboards'")
    print("   3. 查找 'Chat Messages Dashboard'")
    print("   4. 如果没有数据，请先运行聊天测试:")
    print("      python -c \"")
    print("      import asyncio")
    print("      from modules.services.elasticsearch_service import elasticsearch_chat_service")
    print("      asyncio.run(elasticsearch_chat_service.save_conversation(")
    print("          'test-001', 'Hello', 'Hi there!'))\"")

if __name__ == "__main__":
    main()