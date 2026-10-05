# 工具调用系统

## 系统概述

本工具调用系统是智能体系统的一个核心模块，负责管理、决策和执行各种外部工具，使智能体能够根据任务需求自主选择和调用工具。

## 核心组件

### 1. 工具基类 (ToolBase)

所有工具的基类，定义了工具的基本接口。

- **方法**：
  - `execute(**params)`：执行工具，返回执行结果
  - `get_info()`：获取工具信息

### 2. 具体工具实现

#### APIRequestTool
- 用于发送API请求，获取外部数据
- 支持GET、POST等HTTP方法

#### DatabaseQueryTool
- 用于执行数据库查询
- 支持自定义数据库连接函数

#### LocalCommandTool
- 用于执行本地命令
- 支持命令执行和超时控制

### 3. 工具管理器 (ToolManager)

负责工具的注册、管理和执行。

- **核心功能**：
  - 工具注册与注销
  - 工具执行（带权限控制和超时处理）
  - 执行历史记录
  - 权限管理

### 4. 工具决策器 (ToolDecider)

负责分析用户输入和上下文，决定是否需要调用工具。

- **核心功能**：
  - 工具调用需求检测
  - 工具参数提取
  - 工具选择
  - 工具执行结果处理
  - 工具使用建议

## 系统架构

```
智能体系统
  └── 工具调用系统
      ├── ToolManager（工具管理器）
      │   ├── 工具注册与管理
      │   ├── 工具执行（带权限控制和超时处理）
      │   └── 执行历史记录
      ├── ToolDecider（工具决策器）
      │   ├── 用户输入分析
      │   ├── 工具需求检测
      │   ├── 参数提取
      │   └── 结果处理
      └── 工具实现
          ├── APIRequestTool（API请求工具）
          ├── DatabaseQueryTool（数据库查询工具）
          └── LocalCommandTool（本地命令工具）
```

## 使用方法

### 1. 初始化工具系统

```python
from app.modules.tool import ToolManager, ToolDecider

# 初始化工具管理器
tool_manager = ToolManager()

# 初始化工具决策器
tool_decider = ToolDecider(tool_manager=tool_manager)
```

### 2. 注册工具

```python
from app.modules.tool import APIRequestTool, DatabaseQueryTool, LocalCommandTool

# 注册API请求工具
api_tool = APIRequestTool(
    name="api_request",
    description="用于发送API请求，获取外部数据",
    api_url="https://api.example.com",
    method="GET"
)
tool_manager.register_tool(api_tool, permissions=["default", "admin"])

# 注册数据库查询工具
def db_connector(query, args):
    # 实现数据库连接逻辑
    return [{"id": 1, "name": "测试数据"}]

db_tool = DatabaseQueryTool(
    name="database_query",
    description="用于查询数据库，获取数据统计信息",
    db_connector=db_connector
)
tool_manager.register_tool(db_tool, permissions=["admin"])

# 注册本地命令工具
local_tool = LocalCommandTool(
    name="local_command",
    description="用于执行本地命令，检查系统状态"
)
tool_manager.register_tool(local_tool, permissions=["admin"])
```

### 3. 分析用户输入

```python
user_input = "获取天气数据，URL: https://api.weather.com/data，参数: {\"city\": \"北京\"}"
context = []

# 分析用户输入
analysis = tool_decider.analyze_user_input(user_input, context)

if analysis.get('need_tool'):
    # 需要调用工具
    tool_name = analysis['tool_name']
    params = analysis['params']
    print(f"需要调用工具: {tool_name}，参数: {params}")
else:
    print(f"不需要调用工具，原因: {analysis['reason']}")
```

### 4. 执行工具

```python
# 执行工具
result = tool_manager.execute_tool(
    tool_name="api_request",
    params={"city": "北京"},
    user_role="default",
    timeout=30
)

# 处理执行结果
response = tool_decider.handle_tool_result(result, user_input)
print(f"工具执行结果: {response}")
```

### 5. 集成到智能体系统

智能体系统会自动分析用户输入，决定是否需要调用工具，并执行相应的工具调用流程。

## 工具调用流程

1. **输入分析**：分析用户输入，检测是否需要调用工具
2. **参数提取**：从用户输入中提取工具参数
3. **工具选择**：根据工具类型和参数选择合适的工具
4. **权限检查**：检查用户是否有权限执行该工具
5. **工具执行**：执行工具，带超时处理
6. **结果处理**：处理工具执行结果，生成响应
7. **历史记录**：记录工具执行历史

## 性能优化

1. **超时处理**：每个工具执行都有超时限制，避免工具执行时间过长
2. **权限控制**：基于角色的权限控制，确保系统安全
3. **错误处理**：完善的错误处理机制，确保系统稳定性
4. **历史记录**：限制历史记录长度，避免内存占用过大

## 扩展建议

1. **添加更多工具类型**：
   - 文件操作工具
   - 网络爬虫工具
   - 机器学习模型调用工具

2. **增强工具决策能力**：
   - 使用机器学习模型进行工具选择
   - 支持更复杂的工具参数提取

3. **优化工具执行**：
   - 添加工具执行缓存
   - 支持工具执行结果的持久化存储

4. **安全性增强**：
   - 工具执行沙箱
   - 更细粒度的权限控制

## 总结

工具调用系统为智能体提供了与外部世界交互的能力，使智能体能够执行更复杂的任务。通过合理的工具注册和管理，智能体可以根据任务需求自主选择和调用合适的工具，提高系统的灵活性和实用性。