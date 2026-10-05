# 智能科研选题辅助系统部署与验证

本文档用于把代码部署为论文描述的系统形态：Flask API + Vue 前端 + Neo4j 知识图谱 + Redis 会话缓存。

## 1. 基础依赖

在 `project/` 目录执行：

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r web_app\requirements.txt
cd frontend
pnpm install
pnpm build
```

## 2. 配置服务

复制配置模板：

```powershell
Copy-Item config\config.json.example config\config.json
```

编辑 `config/config.json`：

- `model_router.main_model.api_key`
- `model_router.assistant_model.api_key`
- `neo4j.uri`
- `neo4j.username`
- `neo4j.password`
- `redis.url`

论文部署形态要求 Neo4j 与 Redis 均处于可用状态。`/api/health` 中的 `deployment_ready` 只有在 Vue 构建产物、Neo4j、Redis 和智能体全部就绪时才会返回 `true`；否则应先补齐配置或启动对应服务。

## 3. 构建并导入知识图谱

将合法获得的知网/DBLP 元数据导出文件放入：

```text
project/data/kg_sources/
```

支持 JSON/CSV，字段可使用中文或英文，例如 `title/论文题名`、`authors/作者`、`institution/机构`、`keywords/关键词`、`abstract/摘要`、`year/年份`、`venue/期刊`、`funds/基金项目`。

构建 JSON 图谱：

```powershell
python scripts\build_knowledge_graph.py
```

初始化 Neo4j 索引并导入：

```powershell
python scripts\init_neo4j_indexes.py
python scripts\import_knowledge_graph_to_neo4j.py --source data\knowledge_graph.json
```

也可以一条命令构建后导入：

```powershell
python scripts\build_knowledge_graph.py --import-neo4j
```

## 4. 启动系统

开发模式：

```powershell
python web_app\run.py --host 127.0.0.1 -p 5000
```

核心入口：

- `http://127.0.0.1:5000/vue/`
- `http://127.0.0.1:5000/vue/knowledge-graph`
- `http://127.0.0.1:5000/vue/topic-recommendation`
- `http://127.0.0.1:5000/api/health`
- `http://127.0.0.1:5000/api/kg/status`
- `http://127.0.0.1:5000/api/topic/stage/create`

Vue 前端开发模式：

```powershell
cd frontend
pnpm dev
```

生产部署时由 Nginx 托管 `frontend/dist`，并将 `/api/` 代理到 Flask/Gunicorn。

## 5. 性能验证

运行单元测试：

```powershell
pytest tests
```

运行 Locust：

```powershell
locust -f tests\performance\locustfile.py --host http://127.0.0.1:5000
```

建议测试参数：

- 并发用户：50
- 启动速率：10 users/s
- 持续时间：5 分钟

记录聊天、推荐、图谱查询接口的平均响应时间、95 分位和失败率，保存为 `data/performance/` 下的 HTML 或 CSV 报告。
