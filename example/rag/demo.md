# 文档向量化服务使用演示




## 核心功能演示

### 📝 批量创建文档

#### 方式1：自动生成索引（推荐）
```bash
curl -X POST http://localhost:32421/documents \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "title": "人工智能简介",
        "content": "人工智能是计算机科学的一个分支，它企图了解智能的实质...",
        "category": "技术"
      },
      {
        "title": "机器学习基础",
        "content": "机器学习是人工智能的核心技术之一，通过数据训练模型...",
        "category": "技术"
      }
    ],
    "vector_field": "content"
  }'
```

**成功响应：**
```json
{
  "index": "document_20250713_abc1",
  "count": 2
}
```

#### 方式2：指定已存在的索引
```bash
curl -X POST http://localhost:32421/documents \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "title": "深度学习进阶",
        "content": "深度学习是机器学习的一个重要分支..."
      }
    ],
    "vector_field": "content",
    "index": "document_20250713_abc1"
  }'
```

**错误示例（索引不存在）：**
```bash
curl -X POST http://localhost:32421/documents \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [{"title": "test", "content": "test"}],
    "vector_field": "content",
    "index": "nonexistent_index"
  }'
```
返回：
```json
{"detail":"索引 nonexistent_index 不存在，请先创建索引"}
```

### 🔍 文档检索

#### 正确使用（document_开头的索引）
```bash
curl -X POST http://localhost:32421/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "人工智能和机器学习",
    "vector_field": "content",
    "index": "document_20250713_abc1",
    "top_k": 5
  }'
```

**成功响应：**
```json
{
  "results": [
    {
      "score": 1.8234,
      "document": {
        "title": "人工智能简介",
        "content": "人工智能是计算机科学的一个分支...",
        "category": "技术",
        "created_at": "2025-07-13T21:29:35.898391"
      }
    },
    {
      "score": 1.7891,
      "document": {
        "title": "机器学习基础",
        "content": "机器学习是人工智能的核心技术之一...",
        "category": "技术",
        "created_at": "2025-07-13T21:29:35.898397"
      }
    }
  ],
  "total": 2,
  "took": 12
}
```

#### 错误示例（非document_开头的索引）
```bash
curl -X POST http://localhost:32421/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "测试查询",
    "vector_field": "content",
    "index": "invalid_index",
    "top_k": 5
  }'
```
返回：
```json
{"detail":"当前索引: invalid_index不存在，请先创建"}
```

## 重要规则

### ✅ 创建文档规则
- **不指定索引**：自动生成 `document_日期_XXXX` 格式的索引
- **指定索引**：索引必须已存在，否则返回404错误

### ✅ 检索文档规则
- **索引名称**：只能检索以 `document_` 开头的索引
- **索引存在性**：索引必须存在，否则返回404错误

### 📋 字段说明
- `vector_field`: 指定要进行向量化的字段名
- `top_k`: 返回的最相似文档数量（默认5）
- `documents`: 文档数组，每个文档可以包含任意字段

## 完整工作流程示例

```bash
# 1. 检查服务状态
curl http://localhost:32421/health

# 2. 创建文档（自动生成索引）
INDEX_NAME=$(curl -s -X POST http://localhost:32421/documents \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {"title": "Python教程", "content": "Python是一种高级编程语言..."},
      {"title": "Java基础", "content": "Java是一种面向对象的编程语言..."}
    ],
    "vector_field": "content"
  }' | jq -r '.index')

echo "创建的索引: $INDEX_NAME"

# 3. 搜索文档
curl -X POST http://localhost:32421/search \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"编程语言教程\",
    \"vector_field\": \"content\",
    \"index\": \"$INDEX_NAME\",
    \"top_k\": 3
  }"
```

## API文档
访问 `http://localhost:32421/docs` 查看完整的交互式API文档。 