# 选题推荐参考数据库系统

## 系统概述

本系统是一个用于大模型选题推荐参考的简易数据库系统，具备以下核心功能：

- **数据存储与管理**：支持结构化数据存储，包含选题领域分类、关键词、热度指数、时效性评分、相关资源链接等信息字段
- **高效查询检索**：提供多条件组合查询，支持按领域、关键词、热度指数、时效性评分等条件筛选
- **数据更新维护**：支持基础的增删改查操作，确保数据一致性和完整性
- **可扩展性**：系统架构考虑了可扩展性，能够支持后续数据量增长和功能扩展需求
- **性能优化**：在中等数据量下（预计10万级记录）能够在1秒内完成常见查询操作

## 系统架构

### 目录结构

```
topic_recommendation/
├── __init__.py          # 模块初始化文件
├── database.py         # 数据库核心实现
├── api.py              # RESTful API接口
└── README.md           # 系统文档
```

### 技术栈

- **数据库**：SQLite（轻量级、文件型数据库，适合中小规模应用）
- **后端**：Python + Flask
- **API**：RESTful API

## 核心功能

### 1. 数据存储结构

选题数据包含以下字段：

| 字段名 | 类型 | 描述 |
|-------|------|------|
| id | INTEGER | 选题ID（自增主键） |
| title | TEXT | 选题标题 |
| domain | TEXT | 领域分类 |
| subdomain | TEXT | 子领域分类 |
| keywords | TEXT | 关键词（逗号分隔） |
| 热度指数 | REAL | 热度指数（0-10） |
| 时效性评分 | REAL | 时效性评分（0-10） |
| description | TEXT | 选题描述 |
| related_resources | TEXT | 相关资源链接（JSON格式） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 2. 数据库操作

#### 基础操作

- **添加选题**：`add_topic(topic_data)`
- **更新选题**：`update_topic(topic_id, topic_data)`
- **删除选题**：`delete_topic(topic_id)`
- **获取单个选题**：`get_topic(topic_id)`
- **搜索选题**：`search_topics(**kwargs)`
- **获取领域分类**：`get_domains()`
- **获取子领域分类**：`get_subdomains(domain)`
- **获取统计信息**：`get_statistics()`
- **优化数据库**：`optimize_database()`

#### 搜索参数

| 参数 | 类型 | 描述 |
|------|------|------|
| domain | str | 领域分类 |
| keywords | str | 关键词（模糊匹配） |
| min_热度 | float | 最小热度指数 |
| min_时效性 | float | 最小时效性评分 |
| limit | int | 返回数量限制（默认10） |
| offset | int | 偏移量（默认0） |
| order_by | str | 排序字段 |
| order_dir | str | 排序方向（'ASC'或'DESC'） |

### 3. API接口

| 接口路径 | 方法 | 描述 |
|---------|------|------|
| `/api/topic/add` | POST | 添加新选题 |
| `/api/topic/update/<topic_id>` | PUT | 更新选题信息 |
| `/api/topic/delete/<topic_id>` | DELETE | 删除选题 |
| `/api/topic/get/<topic_id>` | GET | 获取单个选题 |
| `/api/topic/search` | GET | 搜索选题 |
| `/api/topic/domains` | GET | 获取所有领域分类 |
| `/api/topic/subdomains/<domain>` | GET | 获取指定领域的子领域分类 |
| `/api/topic/statistics` | GET | 获取数据库统计信息 |
| `/api/topic/optimize` | POST | 优化数据库性能 |

## 使用示例

### 1. 初始化数据库

```python
from app.modules.topic_recommendation import TopicDatabase

# 初始化数据库
db = TopicDatabase()
```

### 2. 添加选题

```python
topic_data = {
    "title": "大语言模型在教育领域的应用研究",
    "domain": "人工智能",
    "subdomain": "自然语言处理",
    "keywords": "大语言模型,教育,应用研究",
    "热度指数": 9.2,
    "时效性评分": 8.8,
    "description": "研究大语言模型如何在教育领域中应用，包括智能辅导、个性化学习等场景",
    "related_resources": [
        {"title": "OpenAI教育应用文档", "url": "https://platform.openai.com/docs/use-cases/education"},
        {"title": "大语言模型教育应用研究", "url": "https://example.com/llm-education-research"}
    ]
}

topic_id = db.add_topic(topic_data)
print(f"添加成功，选题ID: {topic_id}")
```

### 3. 搜索选题

```python
# 搜索人工智能领域的选题，按热度指数降序排序
topics = db.search_topics(
    domain="人工智能",
    min_热度=8.0,
    limit=10,
    order_by="热度指数",
    order_dir="DESC"
)

for topic in topics:
    print(f"{topic['title']} - 热度: {topic['热度指数']}")
```

### 4. API调用示例

#### 添加选题（POST /api/topic/add）

```bash
curl -X POST http://localhost:5000/api/topic/add \
  -H "Content-Type: application/json" \
  -d '{
    "title": "计算机视觉在医疗影像中的应用",
    "domain": "人工智能",
    "subdomain": "计算机视觉",
    "keywords": "计算机视觉,医疗影像,深度学习",
    "热度指数": 8.7,
    "时效性评分": 9.1
  }'
```

#### 搜索选题（GET /api/topic/search）

```bash
curl "http://localhost:5000/api/topic/search?domain=人工智能&keywords=语言模型&min_热度=8.5&limit=5"
```

## 性能优化

1. **索引优化**：为常用查询字段创建索引，包括领域、关键词、热度指数、时效性评分
2. **查询优化**：使用参数化查询，避免SQL注入风险
3. **数据库优化**：提供`optimize_database()`方法，定期运行以保持数据库性能
4. **分页查询**：支持分页功能，避免一次性返回大量数据

## 数据安全

1. **输入验证**：对所有API输入进行验证，确保数据完整性
2. **SQL注入防护**：使用参数化查询，避免SQL注入攻击
3. **错误处理**：统一的错误处理机制，避免敏感信息泄露

## 扩展建议

1. **数据量扩展**：当数据量超过100万时，考虑迁移到更强大的数据库系统（如PostgreSQL）
2. **功能扩展**：
   - 添加用户认证系统
   - 实现数据导出功能
   - 添加数据导入功能
   - 实现更复杂的推荐算法
3. **性能扩展**：
   - 添加缓存层（如Redis）
   - 实现数据库读写分离
   - 考虑使用数据库集群

## 部署说明

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **启动服务**：
   ```bash
   cd web_app
   python run.py
   ```

3. **访问API**：
   - 基础URL: http://localhost:5000/api/topic
   - 文档地址: http://localhost:5000/api/topic/docs

## 总结

本系统为大模型选题推荐提供了一个高效、可靠的数据库支持，具备完整的CRUD操作和查询功能。系统设计考虑了可扩展性和性能优化，能够满足中等规模的数据需求。通过RESTful API接口，大模型可以方便地查询和管理选题数据，为科研选题推荐提供有力支持。
