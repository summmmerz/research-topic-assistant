# 答辩演示步骤

## 1. 启动 Flask 后端

```powershell
cd research-topic-assistant   # 换成你的克隆目录
python web_app\run.py --host 127.0.0.1 -p 5000 --no-check
```

常用入口：

- Vue 主界面：http://127.0.0.1:5000/vue/
- 知识图谱页面：http://127.0.0.1:5000/vue/knowledge-graph
- 分阶段选题推荐：http://127.0.0.1:5000/vue/topic-recommendation
- 健康状态接口：http://127.0.0.1:5000/api/health

## 2. 展示 Neo4j、Redis 与 Vue

`/api/health` 会返回以下内容：

- `services.infrastructure.neo4j`：Neo4j 配置、驱动安装状态和数据库名称。
- `services.infrastructure.redis`：Redis 配置、Python 客户端安装状态和当前会话存储方式。
- `services.infrastructure.vue_frontend`：Vue 构建产物是否存在以及访问路径。
- `services.knowledge_graph.storage`：论文部署形态应为 `neo4j`。
- `services.web_session.session_storage`：论文部署形态应为 `redis`。
- `deployment_ready`：Vue、Neo4j、Redis 和智能体全部就绪时为 `true`。

如果本机未启动 Redis 或未配置 Neo4j 密码，健康接口会返回 `deployment_ready: false`，应先启动服务并导入图谱数据后再作为论文系统演示。

## 3. 构建 Vue 页面

```powershell
cd frontend
npm install
npm run build
```

构建结果会输出到 `web_app/static/vue/`，由 Flask 通过 `/vue/` 路由托管。
