#!/usr/bin/env python3
"""
RAG + LLM 智能问答系统
结合向量检索和大语言模型，实现基于知识库的智能问答
"""

import requests
from openai import OpenAI


class RAGSystem:
    def __init__(
        self,
        rag_base_url="http://nodeport.sensedeal.vip:32421",
        llm_api_key="b9df99ea41435fa7be5ce346b486c33e",
        llm_base_url="https://gateway.chat.sensedeal.vip/v1/",
    ):
        """
        初始化RAG系统

        Args:
            rag_base_url: RAG服务地址
            llm_api_key: LLM API密钥
            llm_base_url: LLM服务地址
        """
        self.rag_base_url = rag_base_url
        self.llm_client = OpenAI(api_key=llm_api_key, base_url=llm_base_url)
        self.index_name = None

    def create_knowledge_base(self, documents, vector_field="content"):
        """
        创建知识库

        Args:
            documents: 文档列表
            vector_field: 向量化字段

        Returns:
            bool: 是否创建成功
        """
        print("📚 正在创建知识库...")

        try:
            response = requests.post(
                f"{self.rag_base_url}/documents",
                headers={"Content-Type": "application/json"},
                json={"documents": documents, "vector_field": vector_field},
            )

            if response.status_code == 200:
                result = response.json()
                self.index_name = result["index"]
                print(f"✅ 知识库创建成功，索引: {self.index_name}")
                print(f"📄 文档数量: {result['count']}")
                return True
            else:
                print(f"❌ 知识库创建失败: {response.json()}")
                return False

        except Exception as e:
            print(f"❌ 创建知识库时出错: {e}")
            return False

    def search_knowledge(self, query, top_k=3):
        """
        在知识库中搜索相关文档

        Args:
            query: 查询文本
            top_k: 返回最相关的文档数量

        Returns:
            list: 相关文档列表
        """
        if not self.index_name:
            print("❌ 知识库未初始化")
            return []

        try:
            response = requests.post(
                f"{self.rag_base_url}/search",
                headers={"Content-Type": "application/json"},
                json={"query": query, "vector_field": "content", "index": self.index_name, "top_k": top_k},
            )

            if response.status_code == 200:
                result = response.json()
                return result["results"]
            else:
                print(f"❌ 搜索失败: {response.json()}")
                return []

        except Exception as e:
            print(f"❌ 搜索时出错: {e}")
            return []

    def generate_answer(self, question, context_docs):
        """
        基于检索到的文档生成答案

        Args:
            question: 用户问题
            context_docs: 检索到的相关文档

        Returns:
            str: 生成的答案
        """
        if not context_docs:
            return "抱歉，我在知识库中没有找到相关信息来回答您的问题。"

        # 构建上下文
        context = "\n".join(
            [
                f"文档{i+1}: {doc['document']['title']}\n内容: {doc['document']['content']}"
                for i, doc in enumerate(context_docs)
            ]
        )

        # 构建提示词
        prompt = f"""基于以下知识库内容回答用户问题。请确保答案准确、简洁，并基于提供的信息。

知识库内容:
{context}

用户问题: {question}

请基于上述知识库内容回答问题。如果知识库中没有足够信息，请说明。"""

        try:
            response = self.llm_client.chat.completions.create(
                model="qwen2.5-32b-instruct-int4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500,
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"❌ 生成答案时出错: {e}"

    def ask(self, question):
        """
        智能问答主函数

        Args:
            question: 用户问题

        Returns:
            dict: 包含答案和相关文档的结果
        """
        print(f"\n🤔 问题: {question}")

        # 1. 检索相关文档
        print("🔍 正在搜索相关文档...")
        relevant_docs = self.search_knowledge(question)

        if relevant_docs:
            print(f"📖 找到 {len(relevant_docs)} 个相关文档:")
            for i, doc in enumerate(relevant_docs, 1):
                score = doc["score"]
                title = doc["document"]["title"]
                print(f"  {i}. [{score:.3f}] {title}")

        # 2. 生成答案
        print("🤖 正在生成答案...")
        answer = self.generate_answer(question, relevant_docs)

        return {"question": question, "answer": answer, "relevant_docs": relevant_docs}


def create_sample_knowledge_base():
    """创建示例知识库"""
    return [
        {
            "title": "Python基础语法",
            "content": "Python是一种解释型、面向对象的编程语言。基本语法包括变量定义、条件语句、循环语句、函数定义等。Python使用缩进来表示代码块，语法简洁易读。",
            "category": "编程语言",
            "difficulty": "初级",
        },
        {
            "title": "机器学习算法",
            "content": "机器学习包括监督学习、无监督学习和强化学习。常见算法有线性回归、决策树、随机森林、支持向量机、神经网络等。每种算法适用于不同类型的问题。",
            "category": "人工智能",
            "difficulty": "中级",
        },
        {
            "title": "深度学习框架",
            "content": "深度学习主要框架包括TensorFlow、PyTorch、Keras等。TensorFlow由Google开发，PyTorch由Facebook开发，都支持GPU加速。Keras是高级API，易于使用。",
            "category": "人工智能",
            "difficulty": "高级",
        },
        {
            "title": "数据库操作",
            "content": "SQL是结构化查询语言，用于管理关系型数据库。基本操作包括SELECT查询、INSERT插入、UPDATE更新、DELETE删除。还有JOIN连接、GROUP BY分组等高级操作。",
            "category": "数据库",
            "difficulty": "中级",
        },
        {
            "title": "Web开发技术",
            "content": "Web开发分为前端和后端。前端技术包括HTML、CSS、JavaScript、React、Vue等。后端技术包括Python Flask/Django、Node.js、Java Spring等。",
            "category": "Web开发",
            "difficulty": "中级",
        },
    ]


def main():
    """主函数演示"""
    print("🚀 RAG + LLM 智能问答系统演示")
    print("=" * 50)

    # 1. 初始化RAG系统
    rag_system = RAGSystem()

    # 2. 创建知识库
    sample_docs = create_sample_knowledge_base()
    if not rag_system.create_knowledge_base(sample_docs):
        print("知识库创建失败，演示终止")
        return

    # 3. 等待索引就绪
    import time

    print("⏳ 等待索引就绪...")
    time.sleep(2)

    # 4. 智能问答演示
    questions = [
        "Python有什么特点？",
        "机器学习有哪些类型？",
        "深度学习框架有哪些？",
        "如何进行数据库查询？",
        "Web开发需要学习什么技术？",
        "如何学习人工智能？",  # 这个问题需要综合多个文档
    ]

    for question in questions:
        result = rag_system.ask(question)
        print(f"\n💡 答案: {result['answer']}")
        print("-" * 50)
        time.sleep(1)  # 避免请求过快

    print("\n✅ 演示完成!")
    print("💡 RAG系统成功结合了向量检索和大语言模型，实现了智能问答")


if __name__ == "__main__":
    main()
