#!/usr/bin/env python3
"""
修复Grafana Elasticsearch数据源的脚本
"""

import requests
import json
import time

# Grafana配置
GRAFANA_URL = "http://localhost:3000"
GRAFANA_AUTH = ("admin", "admin123")

def create_fixed_datasource():
    """创建修复后的Elasticsearch数据源"""
    
    # 删除所有现有的elasticsearch数据源
    try:
        response = requests.get(f"{GRAFANA_URL}/api/datasources", auth=GRAFANA_AUTH)
        if response.status_code == 200:
            datasources = response.json()
            for ds in datasources:
                if "elasticsearch" in ds.get("name", "").lower():
                    delete_response = requests.delete(
                        f"{GRAFANA_URL}/api/datasources/{ds['id']}", 
                        auth=GRAFANA_AUTH
                    )
                    if delete_response.status_code == 200:
                        print(f"✅ 删除了数据源: {ds['name']}")
    except Exception as e:
        print(f"清理数据源时出错: {e}")
    
    # 创建新的正确配置的数据源
    datasource_config = {
        "name": "elasticsearch-chat",
        "type": "elasticsearch", 
        "uid": "elasticsearch-chat",
        "url": "http://elasticsearch:9200",
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
            "includeFrozen": False,
            "xpack": False
        },
        "secureJsonData": {}
    }
    
    try:
        response = requests.post(
            f"{GRAFANA_URL}/api/datasources",
            auth=GRAFANA_AUTH,
            json=datasource_config,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功创建数据源: {result.get('name')} (ID: {result.get('id')})")
            
            # 测试数据源
            time.sleep(2)  # 等待数据源初始化
            test_datasource(result.get('id'))
            
            return result
        else:
            print(f"❌ 创建数据源失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 创建数据源时出错: {e}")
        return None

def test_datasource(datasource_id):
    """测试数据源连接"""
    try:
        # 测试基本连接
        test_url = f"{GRAFANA_URL}/api/datasources/proxy/{datasource_id}/_cluster/health"
        response = requests.get(test_url, auth=GRAFANA_AUTH, timeout=10)
        
        if response.status_code == 200:
            health = response.json()
            print(f"✅ 集群连接测试成功: {health.get('status', 'unknown')}")
        else:
            print(f"⚠️  集群连接测试: {response.status_code}")
        
        # 测试数据查询
        search_url = f"{GRAFANA_URL}/api/datasources/proxy/{datasource_id}/chat-*/_search"
        search_body = {"size": 1, "query": {"match_all": {}}}
        
        response = requests.post(
            search_url, 
            auth=GRAFANA_AUTH,
            json=search_body,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            total = result.get("hits", {}).get("total", {}).get("value", 0)
            print(f"✅ 数据查询测试成功: 找到 {total} 条记录")
        else:
            print(f"⚠️  数据查询测试: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试数据源时出错: {e}")

def create_simple_dashboard(datasource_uid):
    """创建简化的Dashboard"""
    
    dashboard_json = {
        "dashboard": {
            "id": None,
            "title": "Chat Messages - Fixed",
            "tags": ["elasticsearch", "chat", "fixed"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "Message Count",
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
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None}
                                ]
                            }
                        }
                    },
                    "options": {
                        "reduceOptions": {
                            "values": False,
                            "calcs": ["lastNotNull"],
                            "fields": ""
                        },
                        "orientation": "auto",
                        "textMode": "auto"
                    }
                },
                {
                    "id": 2,
                    "title": "Recent Messages",
                    "type": "table",
                    "gridPos": {"h": 8, "w": 18, "x": 6, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "datasource": {"uid": datasource_uid},
                            "query": "*",
                            "metrics": [
                                {
                                    "id": "1", 
                                    "type": "raw_data",
                                    "settings": {"size": 5}
                                }
                            ],
                            "bucketAggs": [],
                            "timeField": "timestamp"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "custom": {"align": "auto", "displayMode": "auto"},
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [{"color": "green", "value": None}]
                            }
                        }
                    },
                    "options": {"showHeader": True}
                }
            ],
            "time": {"from": "now-24h", "to": "now"},
            "refresh": "30s",
            "schemaVersion": 27,
            "version": 0
        },
        "overwrite": True
    }
    
    try:
        response = requests.post(
            f"{GRAFANA_URL}/api/dashboards/db",
            auth=GRAFANA_AUTH,
            json=dashboard_json,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            dashboard_url = f"{GRAFANA_URL}{result.get('url', '')}"
            print(f"✅ 成功创建Dashboard: Chat Messages - Fixed")
            print(f"📊 访问地址: {dashboard_url}")
            return result
        else:
            print(f"❌ 创建Dashboard失败: {response.status_code}")
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"❌ 创建Dashboard时出错: {e}")
    
    return None

def main():
    """主函数"""
    print("🔧 修复Grafana Elasticsearch数据源...")
    print()
    
    # 创建修复后的数据源
    datasource = create_fixed_datasource()
    if not datasource:
        print("❌ 无法创建数据源，退出")
        return
    
    print()
    
    # 创建简化Dashboard
    print("📊 创建修复后的Dashboard...")
    dashboard = create_simple_dashboard(datasource.get("uid"))
    
    print()
    print("✨ 修复完成！")
    print()
    print("🌐 访问信息:")
    print(f"   Grafana: {GRAFANA_URL}")
    print(f"   用户名: admin / 密码: admin123")
    print()
    print("📋 下一步:")
    print("   1. 访问Grafana")
    print("   2. 查找 'Chat Messages - Fixed' Dashboard")
    print("   3. 检查数据是否正确显示")

if __name__ == "__main__":
    main()