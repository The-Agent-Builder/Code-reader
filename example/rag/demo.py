#!/usr/bin/env python3
"""
文档向量化服务使用演示脚本
"""

import requests
import json
import time

# 服务配置
BASE_URL = "http://nodeport.sensedeal.vip:32421"

def check_health():
    """检查服务健康状态"""
    print("🔍 检查服务健康状态...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ 服务运行正常")
            return True
        else:
            print(f"❌ 服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接服务: {e}")
        return False

def create_documents():
    """演示创建文档功能"""
    print("\n📝 演示创建文档功能...")
    
    # 示例文档数据
    documents_data = {
        "documents": [
            {
                "title": "Python编程入门",
                "content": "Python是一种高级编程语言，语法简洁明了，适合初学者学习。它广泛应用于数据科学、人工智能、Web开发等领域。",
                "category": "编程",
                "difficulty": "初级"
            },
            {
                "title": "机器学习基础",
                "content": "机器学习是人工智能的核心技术之一，通过算法让计算机从数据中学习模式。包括监督学习、无监督学习和强化学习。",
                "category": "AI",
                "difficulty": "中级"
            },
            {
                "title": "深度学习进阶",
                "content": "深度学习使用神经网络模型处理复杂数据，在图像识别、自然语言处理等领域取得突破性进展。",
                "category": "AI",
                "difficulty": "高级"
            }
        ],
        "vector_field": "content"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/documents",
            headers={"Content-Type": "application/json"},
            json=documents_data
        )
        
        if response.status_code == 200:
            result = response.json()
            index_name = result["index"]
            count = result["count"]
            print(f"✅ 成功创建 {count} 个文档")
            print(f"📂 索引名称: {index_name}")
            return index_name
        else:
            print(f"❌ 创建文档失败: {response.json()}")
            return None
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

def search_documents(index_name):
    """演示搜索文档功能"""
    print(f"\n🔍 演示搜索文档功能...")
    
    # 不同的搜索查询
    queries = [
        "Python编程语言",
        "人工智能和机器学习",
        "神经网络深度学习",
        "数据科学应用"
    ]
    
    for query in queries:
        print(f"\n🔎 搜索查询: '{query}'")
        
        search_data = {
            "query": query,
            "vector_field": "content",
            "index": index_name,
            "top_k": 2
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/search",
                headers={"Content-Type": "application/json"},
                json=search_data
            )
            
            if response.status_code == 200:
                result = response.json()
                results = result["results"]
                total = result["total"]
                took = result["took"]
                
                print(f"📊 找到 {total} 个相关文档，耗时 {took}ms")
                
                for i, item in enumerate(results, 1):
                    score = item["score"]
                    doc = item["document"]
                    print(f"  {i}. [{score:.4f}] {doc['title']}")
                    print(f"     类别: {doc.get('category', 'N/A')} | 难度: {doc.get('difficulty', 'N/A')}")
                    
            else:
                print(f"❌ 搜索失败: {response.json()}")
                
        except Exception as e:
            print(f"❌ 搜索请求失败: {e}")
        
        time.sleep(0.5)  # 避免请求过快

def demo_error_cases():
    """演示错误情况"""
    print(f"\n⚠️ 演示错误情况...")
    
    # 1. 指定不存在的索引创建文档
    print("\n1️⃣ 指定不存在的索引创建文档:")
    try:
        response = requests.post(
            f"{BASE_URL}/documents",
            headers={"Content-Type": "application/json"},
            json={
                "documents": [{"title": "测试", "content": "测试内容"}],
                "vector_field": "content",
                "index": "nonexistent_index"
            }
        )
        print(f"   结果: {response.json()}")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 2. 搜索非document_开头的索引
    print("\n2️⃣ 搜索非document_开头的索引:")
    try:
        response = requests.post(
            f"{BASE_URL}/search",
            headers={"Content-Type": "application/json"},
            json={
                "query": "测试查询",
                "vector_field": "content",
                "index": "invalid_index",
                "top_k": 5
            }
        )
        print(f"   结果: {response.json()}")
    except Exception as e:
        print(f"   错误: {e}")

def main():
    """主函数"""
    print("🚀 文档向量化服务演示")
    print("=" * 50)
    
    # 1. 检查服务状态
    if not check_health():
        print("请先启动服务: python main.py")
        return
    
    # 2. 创建文档
    index_name = create_documents()
    if not index_name:
        print("创建文档失败，演示终止")
        return
    
    # 等待索引就绪
    print("\n⏳ 等待索引就绪...")
    time.sleep(2)
    
    # 3. 搜索文档
    search_documents(index_name)
    
    # 4. 演示错误情况
    demo_error_cases()
    
    print("\n✅ 演示完成!")
    print(f"💡 可以访问 {BASE_URL}/docs 查看完整API文档")

if __name__ == "__main__":
    main() 