# Locust 性能测试说明

本目录用于论文测试章节的并发访问、吞吐量、响应时间和失败率验证。主脚本为 `locustfile.py`，覆盖系统首页、知识图谱、选题推荐、会话设置、历史记录和少量智能问答请求。

## 启动被测系统

从 `project/` 目录启动 Web 服务：

```powershell
python web_app/run.py --host 127.0.0.1 -p 5000
```

## Web 控制台模式

从 `project/` 目录运行：

```powershell
locust -f tests/performance/locustfile.py --host http://127.0.0.1:5000
```

如果在仓库根目录运行，也可以直接使用根目录包装入口：

```powershell
locust --host http://127.0.0.1:5000
```

浏览器打开 `http://localhost:8089`，设置并发用户数和启动速率后开始测试。

## 无界面模式

下面命令适合直接产出论文截图和 CSV 数据：

```powershell
locust -f tests/performance/locustfile.py --host http://127.0.0.1:5000 --headless -u 50 -r 5 -t 5m --csv data/locust_thesis_50u
```

建议分别运行 20、50、100 个用户的阶梯测试，并记录：

- 平均响应时间
- P95 响应时间
- Requests/s
- 失败率
- 各接口响应时间对比

聊天接口依赖智能体和外部模型配置，若本地模型/API 不稳定，可在论文中单独说明，并重点使用知识图谱与选题推荐接口作为稳定性能样本。
