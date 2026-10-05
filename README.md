# 智能科研选题助手

## 项目概述

智能科研选题助手是一个基于人工智能技术的科研辅助平台，旨在帮助研究人员快速获取科研选题灵感、分析学术趋势、探索知识网络。该平台集成了智能聊天助手、知识图谱可视化和选题推荐等核心功能，为科研工作者提供全方位的科研支持。

### 核心价值
- **智能选题推荐**：基于知识图谱和AI分析，提供个性化的科研选题建议
- **知识网络可视化**：直观展示学术实体之间的关联关系，帮助发现研究热点
- **实时智能对话**：支持自然语言交互，解答科研相关问题
- **学术资源整合**：聚合多维度学术信息，提供全面的科研参考

## 项目结构

```
project/
├── app/                    # 核心应用代码
│   ├── config/             # 配置管理模块
│   ├── core/               # 核心功能模块
│   │   ├── agent.py        # 智能体实现
│   │   └── context.py      # 上下文管理
│   ├── modules/            # 功能模块
│   │   ├── knowledge_graph/  # 知识图谱模块
│   │   ├── topic_recommendation/  # 选题推荐模块
│   │   ├── tool/           # 工具模块
│   │   ├── model/          # 模型管理
│   │   ├── response/       # 响应生成
│   │   └── retrieval/      # 文档检索
│   └── utils/              # 工具函数
├── web_app/                # Web应用
│   ├── static/             # 静态资源
│   ├── templates/          # HTML模板
│   ├── utils/              # Web工具
│   ├── app.py              # Web应用入口
│   └── requirements.txt    # Web依赖
├── data/                   # 数据目录
│   ├── kg_sources/         # 知识图谱源数据
│   ├── exports/            # 导出数据
│   └── knowledge_graph.json  # 知识图谱数据
├── scripts/                # 脚本工具
├── config/                 # 配置文件
├── requirements.txt        # 项目依赖
└── main.py                 # 主入口
```

### 主要模块说明

| 模块 | 主要职责 | 文件位置 | 功能说明 |
|------|---------|---------|--------|
| 智能聊天 | 提供自然语言交互 | app/core/agent.py | 处理用户输入，生成智能回复 |
| 知识图谱 | 学术知识网络构建与可视化 | app/modules/knowledge_graph/ | 管理实体关系，提供可视化数据 |
| 选题推荐 | 科研选题智能推荐 | app/modules/topic_recommendation/ | 基于知识图谱分析推荐选题 |
| Web应用 | 用户界面与API接口 | web_app/app.py | 提供Web界面和RESTful API |
| 数据管理 | 知识图谱数据存储 | data/knowledge_graph.json | 存储实体和关系数据 |

## 功能特性

### 核心功能

1. **智能聊天助手**
   - 支持自然语言交互
   - 流式输出，实时显示回复
   - 会话管理与历史记录
   - 个性化设置

2. **知识图谱可视化**
   - 实体关系网络展示
   - 多维度实体类型（论文、作者、机构、关键词等）
   - 交互式搜索与筛选
   - 实体详情查看

3. **选题推荐系统**
   - 基于知识图谱的智能推荐
   - 热点趋势分析
   - 个性化选题建议

4. **数据管理**
   - 知识图谱数据导入与更新
   - 数据导出（JSON、CSV格式）
   - 统计分析

### 扩展功能

1. **API接口**
   - RESTful API设计
   - WebSocket实时通信
   - 健康检查与状态监控

2. **用户体验**
   - 响应式设计，支持多设备
   - 主题切换（明暗模式）
   - 动画效果与交互反馈

3. **系统管理**
   - 会话管理与清理
   - 请求统计与监控
   - 错误处理与日志

## 环境要求

- Python 3.8+
- Flask 3.0.0+
- 可选：Neo4j数据库（用于知识图谱存储）

### 依赖包

| 类别 | 依赖 | 版本 | 用途 |
|------|------|------|------|
| 核心框架 | Flask | 3.0.0 | Web应用框架 |
| 网络通信 | Flask-CORS | 4.0.0 | 跨域资源共享 |
|  | Flask-SocketIO | 5.3.6 | 实时通信 |
|  | python-socketio | 5.10.0 | SocketIO客户端 |
| 知识图谱 | neo4j | 5.15.0 | 图数据库（可选） |
|  | jieba | 0.42.1 | 中文分词 |
| 工具 | python-dotenv | 1.0.0 | 环境变量管理 |
| 开发 | pytest | 7.4.0 | 测试框架 |
|  | black | 23.9.1 | 代码格式化 |
|  | flake8 | 6.1.0 | 代码检查 |
| 文档 | mkdocs | 1.5.3 | 文档生成 |
|  | mkdocs-material | 9.4.1 | 文档主题 |

## 安装步骤

### 1. 克隆项目

```bash
git clone <项目地址>
cd project
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# 安装Web应用依赖
pip install -r web_app/requirements.txt
```

### 4. 配置环境

**密钥只放 `.env`，不要写进 `config/config.json`。** 配置优先级：环境变量 > 配置文件 > 默认值。

```bash
# 1) 复制配置文件（保持 .example 里的占位符即可）
cp config/config.json.example config/config.json

# 2) 复制环境变量示例并填入真实密钥
cp .env.example .env
```

`.env` 里需要填的项：

| 变量 | 说明 |
|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥（对话与选题生成） |
| `NEO4J_PASSWORD` | Neo4j 密码（`NEO4J_URI`/`NEO4J_USER`/`NEO4J_DATABASE` 有默认值，可选填） |
| `REDIS_URL` | 可选，默认 `redis://localhost:6379/0` |

`.env` 与 `config/config.json` 都已在 `.gitignore` 中，不会被提交。

### 5. 初始化知识图谱

```bash
python scripts/init_knowledge_graph.py
```

## 使用方法

### 启动Web服务器

```bash
# 方法1：直接运行
python web_app/app.py

# 方法2：使用gunicorn（生产环境）
gunicorn -w 4 web_app.app:app
```

服务器启动后，访问：
- 主界面：http://localhost:5000
- 知识图谱：http://localhost:5000/knowledge-graph

### API接口

#### 聊天接口

**POST /api/chat**
- 非流式聊天接口
- 请求体：`{"message": "你的问题", "session_id": "会话ID"}`
- 响应：智能回复内容

**POST /api/chat/stream**
- 流式聊天接口（Server-Sent Events）
- 请求体：`{"message": "你的问题", "session_id": "会话ID"}`
- 响应：流式输出的回复内容

#### 知识图谱接口

**GET /api/kg/status**
- 获取知识图谱状态
- 响应：实体和关系统计信息

**GET /api/kg/visualization**
- 获取知识图谱可视化数据
- 参数：`entity_types`（实体类型）、`max_nodes`（最大节点数）
- 响应：节点和边的JSON数据

**POST /api/kg/search**
- 搜索实体
- 请求体：`{"query": "搜索关键词", "entity_types": ["类型1", "类型2"]}`
- 响应：搜索结果列表

#### 系统接口

**GET /api/status**
- 获取系统状态
- 响应：系统运行状态和统计信息

**GET /api/history**
- 获取聊天历史
- 参数：`session_id`（会话ID）、`limit`（限制数量）
- 响应：历史消息列表

**POST /api/settings**
- 更新用户设置
- 请求体：`{"session_id": "会话ID", "settings": {"theme": "light", "stream_output": true}}`
- 响应：更新后的设置

### 示例命令

#### 初始化知识图谱

```bash
python scripts/init_knowledge_graph.py
```

#### 运行Web应用

```bash
python web_app/app.py
```

#### 测试API接口

```bash
# 测试聊天接口
curl -X POST http://localhost:5000/api/chat -H "Content-Type: application/json" -d '{"message": "什么是人工智能", "session_id": "test"}'

# 测试知识图谱状态
curl http://localhost:5000/api/kg/status

# 测试知识图谱可视化数据
curl "http://localhost:5000/api/kg/visualization?max_nodes=100"
```

## 常见问题解答

### Q: 服务器启动失败怎么办？

**A:** 检查以下几点：
- 确认Python环境正确安装
- 检查依赖包是否完整安装
- 确认端口5000未被占用
- 查看控制台错误信息

### Q: 知识图谱页面显示空白怎么办？

**A:** 可能的原因：
- 知识图谱数据未初始化
- API请求失败
- 前端JavaScript错误
- 检查浏览器控制台错误信息

### Q: 聊天功能无法使用怎么办？

**A:** 检查：
- 智能体是否初始化完成
- 网络连接是否正常
- WebSocket连接是否成功

### Q: 如何添加自定义知识图谱数据？

**A:** 将数据文件放入 `data/kg_sources/` 目录，然后运行：

```bash
python scripts/init_knowledge_graph.py
```

### Q: 如何导出知识图谱数据？

**A:** 使用知识图谱页面的导出功能，或调用API：

```bash
curl -X POST http://localhost:5000/api/kg/export/json -H "Content-Type: application/json" -d '{}'
```

## 贡献指南

### 开发流程

1. **Fork项目**
2. **创建分支**：`git checkout -b feature/your-feature`
3. **开发功能**
4. **代码检查**：运行 `flake8` 和 `black`
5. **提交代码**：`git commit -m "Add feature: your feature"`
6. **推送分支**：`git push origin feature/your-feature`
7. **创建Pull Request**

### 代码规范

- 使用 `black` 进行代码格式化
- 遵循 PEP 8 代码风格
- 添加适当的文档字符串
- 编写单元测试

### 功能扩展

如果您希望扩展功能，建议：
- 在 `app/modules/` 目录下创建新模块
- 遵循现有的代码结构和命名规范
- 添加相应的API接口
- 更新文档

## 版权信息

© 2026 智能科研选题助手

本项目采用 MIT 许可证，详情请参阅 LICENSE 文件。

### 免责声明

- 本项目仅供学术研究和学习使用
- 数据来源于公开学术资源，如有侵权请联系删除
- 智能推荐功能基于算法分析，仅供参考，不构成学术建议

## 联系方式

- 项目地址：<https://github.com/summmmerz/research-topic-assistant>
- 问题反馈：<https://github.com/summmmerz/research-topic-assistant/issues>

---

**感谢您使用智能科研选题助手！** 我们致力于为科研工作者提供更智能、更高效的科研辅助工具。如有任何问题或建议，欢迎随时联系我们。