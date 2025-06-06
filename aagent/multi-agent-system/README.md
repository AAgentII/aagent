# Multi-Agent Orchestration System

一个基于可视化工作流的多Agent协作系统，支持拖拽式节点编排、任务分解、并行执行和智能验证。

## 🌟 核心特性

- **可视化工作流编辑器** - 基于ReactFlow的拖拽式节点编排
- **多Agent角色系统** - 协调者、监督者、执行者、验证者等专业化Agent
- **智能任务分解** - 自动将复杂任务分解为可执行的子任务
- **并行执行引擎** - 支持条件分支、并行执行和智能路由
- **实时监控面板** - WebSocket实时推送执行状态
- **MCP协议支持** - 标准化的工具调用接口
- **沙箱执行环境** - 安全的代码执行和工具调用
- **完整的测试覆盖** - 单元测试和集成测试

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Workflow   │  │   Visual     │  │    Monitoring    │  │
│  │   Editor    │  │   Canvas     │  │    Dashboard     │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ WebSocket / REST API
┌─────────────────────────┴───────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Workflow   │  │    Agent     │  │    Execution     │  │
│  │   Engine    │  │   System     │  │     Engine       │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │     MCP     │  │   Tool       │  │    Vector        │  │
│  │  Protocol   │  │  Registry    │  │    Database      │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### 使用Docker Compose启动

```bash
# 克隆项目
git clone <repository-url>
cd aagent/multi-agent-system

# 复制环境配置
cp backend/.env.example backend/.env

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 本地开发环境

#### 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn main:app --reload
```

#### 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 📋 API文档

启动后访问以下地址：

- API文档: http://localhost:8000/docs
- 前端应用: http://localhost:3000
- Flower监控: http://localhost:5555

## 🧪 测试

### 运行后端测试

```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_agents.py -v

# 查看测试覆盖率
pytest --cov=. --cov-report=html
```

### 测试用例示例

```python
# 测试多Agent协作
async def test_multi_agent_collaboration():
    coordinator = CoordinatorAgent(config)
    worker = WorkerAgent(config)
    validator = ValidatorAgent(config)
    
    # 协调者分解任务
    task = {"type": "decompose", "description": "..."}
    decomposition = await coordinator.process(task)
    
    # Worker执行任务
    result = await worker.process(decomposition.data["subtasks"][0])
    
    # 验证者验证结果
    validation = await validator.process({
        "type": "validate_output",
        "output": result.data
    })
```

## 🎯 使用示例

### 1. 创建工作流

```javascript
// 定义工作流节点
const nodes = [
  { id: 'start', type: 'start', position: { x: 100, y: 100 } },
  { id: 'coord', type: 'agent', data: { 
    label: 'Coordinator',
    agent_config: { role: 'coordinator' }
  }},
  { id: 'worker1', type: 'agent', data: {
    label: 'Data Collector',
    agent_config: { role: 'worker', tools: ['web_search'] }
  }},
  { id: 'validator', type: 'agent', data: {
    label: 'Quality Checker',
    agent_config: { role: 'validator' }
  }},
  { id: 'end', type: 'end', position: { x: 500, y: 300 } }
];

// 定义连接
const edges = [
  { source: 'start', target: 'coord' },
  { source: 'coord', target: 'worker1' },
  { source: 'worker1', target: 'validator' },
  { source: 'validator', target: 'end' }
];
```

### 2. 执行工作流

```python
# 使用API执行工作流
import requests

response = requests.post('http://localhost:8000/api/executions', json={
    'workflow_id': 'your-workflow-id',
    'input_data': {
        'task': 'Analyze competitor pricing strategies',
        'requirements': {
            'competitors': ['Company A', 'Company B'],
            'data_points': ['pricing', 'features', 'market_share']
        }
    }
})

execution_id = response.json()['id']
```

### 3. 监控执行状态

```javascript
// WebSocket连接监控
const ws = new WebSocket(`ws://localhost:8000/api/executions/${executionId}/stream`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Execution update:', data);
  
  if (data.type === 'execution_completed') {
    console.log('Results:', data.results);
  }
};
```

## 🛠️ 配置说明

### Agent配置

```python
# 创建自定义Agent
agent_config = {
    "name": "research_expert",
    "role": "researcher",
    "model": "claude-3-sonnet",
    "temperature": 0.3,
    "system_prompt": "You are an expert researcher...",
    "tools": ["web_search", "pdf_reader", "data_analyzer"]
}
```

### 工作流配置

```json
{
  "name": "Market Analysis Workflow",
  "description": "Comprehensive market analysis pipeline",
  "nodes": [...],
  "edges": [...],
  "config": {
    "max_parallel_executions": 5,
    "timeout_seconds": 3600,
    "retry_policy": {
      "max_retries": 3,
      "backoff_factor": 2
    }
  }
}
```

## 📊 性能优化

- **并行执行** - 自动识别可并行的任务节点
- **缓存机制** - Redis缓存频繁访问的数据
- **连接池** - 数据库和Redis连接池管理
- **异步处理** - 全异步架构，高并发支持

## 🔒 安全特性

- JWT认证
- 角色权限控制
- API访问限流
- 沙箱代码执行
- 输入验证和清理

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [ReactFlow](https://reactflow.dev/) - 优秀的流程图库
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能Web框架
- [Anthropic Claude](https://www.anthropic.com/) - 强大的AI模型
- [shadcn/ui](https://ui.shadcn.com/) - 精美的UI组件