# 多Agent可视化编排系统 - 快速启动指南

## 项目结构

```bash
multi-agent-orchestration/
├── backend/                    # 后端服务
│   ├── core/                  # 核心模块
│   │   ├── agents/           # Agent实现
│   │   ├── workflow/         # 工作流引擎
│   │   ├── tools/           # 工具集成
│   │   └── sandbox/         # 执行沙盒
│   ├── api/                 # API接口
│   ├── services/           # 业务服务
│   └── models/             # 数据模型
├── frontend/               # 前端界面
│   ├── components/        # UI组件
│   │   ├── flow-editor/  # 可视化编辑器
│   │   ├── agent-nodes/ # Agent节点
│   │   └── dashboard/   # 监控面板
│   ├── lib/             # 工具库
│   └── pages/           # 页面
├── shared/              # 共享类型定义
├── docker/              # Docker配置
├── docs/                # 文档
└── examples/            # 示例
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/your-org/multi-agent-orchestration.git
cd multi-agent-orchestration

# 安装依赖
pip install -r requirements.txt
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置必要的API密钥
```

### 2. 启动服务

```bash
# 使用Docker Compose启动所有服务
docker-compose up -d

# 或者分别启动
# 后端服务
cd backend && uvicorn main:app --reload --port 8000

# 前端服务
cd frontend && npm run dev
```

## 核心模块实现

### 1. Agent基础实现

```python
# backend/core/agents/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
import asyncio
from pydantic import BaseModel

class AgentRole(Enum):
    COORDINATOR = "coordinator"
    SUPERVISOR = "supervisor"
    WORKER = "worker"
    VALIDATOR = "validator"
    RESEARCHER = "researcher"
    ANALYZER = "analyzer"

class AgentConfig(BaseModel):
    name: str
    role: AgentRole
    model: str = "gpt-4"
    temperature: float = 0.7
    tools: List[str] = []
    max_iterations: int = 10
    system_prompt: Optional[str] = None

class AgentMessage(BaseModel):
    id: str
    from_agent: str
    to_agent: str
    content: Any
    timestamp: float
    message_type: str = "task"

class BaseAgent(ABC):
    def __init__(self, config: AgentConfig):
        self.config = config
        self.id = f"{config.role.value}_{config.name}"
        self.message_queue = asyncio.Queue()
        self.tools = self._load_tools(config.tools)
        self.memory = []
        
    def _load_tools(self, tool_names: List[str]) -> Dict[str, Any]:
        """加载工具"""
        from ..tools import ToolRegistry
        tools = {}
        for tool_name in tool_names:
            tool = ToolRegistry.get_tool(tool_name)
            if tool:
                tools[tool_name] = tool
        return tools
    
    @abstractmethod
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务的核心方法"""
        pass
    
    async def receive_message(self, message: AgentMessage):
        """接收消息"""
        await self.message_queue.put(message)
    
    async def send_message(self, to_agent: str, content: Any):
        """发送消息给其他Agent"""
        from ..workflow import MessageBus
        message = AgentMessage(
            id=str(uuid.uuid4()),
            from_agent=self.id,
            to_agent=to_agent,
            content=content,
            timestamp=time.time()
        )
        await MessageBus.publish(message)
```

### 2. 专业化Agent实现

```python
# backend/core/agents/specialized.py
from .base import BaseAgent, AgentRole, AgentConfig
from typing import Dict, Any, List
import json

class CoordinatorAgent(BaseAgent):
    """协调者Agent - 负责任务分解和分配"""
    
    def __init__(self, config: AgentConfig):
        config.role = AgentRole.COORDINATOR
        super().__init__(config)
        self.task_queue = []
        self.agent_assignments = {}
    
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # 1. 分析任务复杂度
        complexity = await self._analyze_task_complexity(task)
        
        # 2. 分解任务
        subtasks = await self._decompose_task(task, complexity)
        
        # 3. 分配任务给合适的Agent
        assignments = await self._assign_tasks(subtasks)
        
        # 4. 协调执行
        results = await self._coordinate_execution(assignments)
        
        return {
            "status": "completed",
            "subtasks": len(subtasks),
            "assignments": assignments,
            "results": results
        }
    
    async def _analyze_task_complexity(self, task: Dict[str, Any]) -> str:
        # 使用LLM分析任务复杂度
        prompt = f"""
        Analyze the complexity of this task:
        {json.dumps(task, indent=2)}
        
        Rate complexity as: simple, moderate, or complex
        Consider factors like:
        - Number of steps required
        - Domain expertise needed
        - Data processing requirements
        """
        
        # 调用LLM
        response = await self._call_llm(prompt)
        return response.get("complexity", "moderate")
    
    async def _decompose_task(self, task: Dict[str, Any], complexity: str) -> List[Dict]:
        prompt = f"""
        Decompose this {complexity} task into subtasks:
        {json.dumps(task, indent=2)}
        
        Return a JSON array of subtasks with:
        - name: subtask name
        - description: what needs to be done
        - required_skills: list of required capabilities
        - dependencies: list of other subtask names this depends on
        """
        
        response = await self._call_llm(prompt, response_format="json")
        return response.get("subtasks", [])

class SupervisorAgent(BaseAgent):
    """监督者Agent - 监控执行质量"""
    
    def __init__(self, config: AgentConfig):
        config.role = AgentRole.SUPERVISOR
        super().__init__(config)
        self.monitoring_tasks = {}
    
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type", "monitor")
        
        if task_type == "monitor":
            return await self._monitor_execution(task)
        elif task_type == "review":
            return await self._review_results(task)
        
    async def _monitor_execution(self, task: Dict[str, Any]) -> Dict[str, Any]:
        worker_id = task.get("worker_id")
        task_id = task.get("task_id")
        
        # 设置监控
        self.monitoring_tasks[task_id] = {
            "worker_id": worker_id,
            "start_time": time.time(),
            "checkpoints": []
        }
        
        # 定期检查进度
        while task_id in self.monitoring_tasks:
            await asyncio.sleep(5)  # 每5秒检查一次
            status = await self._check_worker_status(worker_id, task_id)
            
            if status.get("completed"):
                return await self._review_results({
                    "task_id": task_id,
                    "results": status.get("results")
                })

class ValidatorAgent(BaseAgent):
    """验证者Agent - 验证结果质量"""
    
    def __init__(self, config: AgentConfig):
        config.role = AgentRole.VALIDATOR
        super().__init__(config)
        self.validation_criteria = {}
    
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        result_to_validate = task.get("result")
        criteria = task.get("criteria", {})
        
        validation_results = {
            "accuracy": await self._validate_accuracy(result_to_validate, criteria),
            "completeness": await self._validate_completeness(result_to_validate, criteria),
            "quality": await self._validate_quality(result_to_validate, criteria)
        }
        
        overall_score = sum(validation_results.values()) / len(validation_results)
        
        return {
            "status": "validated",
            "scores": validation_results,
            "overall_score": overall_score,
            "passed": overall_score >= 0.8,
            "feedback": await self._generate_feedback(validation_results, result_to_validate)
        }
```

### 3. 工作流引擎实现

```python
# backend/core/workflow/engine.py
from typing import Dict, List, Any, Optional
import asyncio
from dataclasses import dataclass
import networkx as nx

@dataclass
class WorkflowNode:
    id: str
    type: str  # agent, condition, parallel, join
    agent_config: Optional[Dict] = None
    condition: Optional[str] = None

@dataclass
class WorkflowEdge:
    from_node: str
    to_node: str
    condition: Optional[str] = None

class WorkflowEngine:
    def __init__(self):
        self.agents = {}
        self.graph = nx.DiGraph()
        self.execution_context = {}
        
    def load_workflow(self, workflow_definition: Dict):
        """加载工作流定义"""
        # 创建节点
        for node in workflow_definition["nodes"]:
            self.graph.add_node(
                node["id"],
                data=WorkflowNode(**node)
            )
            
            # 如果是Agent节点，创建Agent实例
            if node["type"] == "agent":
                agent = self._create_agent(node["agent_config"])
                self.agents[node["id"]] = agent
        
        # 创建边
        for edge in workflow_definition["edges"]:
            self.graph.add_edge(
                edge["from_node"],
                edge["to_node"],
                condition=edge.get("condition")
            )
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        self.execution_context = {"input": input_data, "results": {}}
        
        # 找到起始节点
        start_nodes = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
        
        # 并发执行起始节点
        tasks = []
        for node_id in start_nodes:
            task = asyncio.create_task(self._execute_node(node_id))
            tasks.append(task)
        
        # 等待所有任务完成
        await asyncio.gather(*tasks)
        
        return self.execution_context["results"]
    
    async def _execute_node(self, node_id: str):
        """执行单个节点"""
        node_data = self.graph.nodes[node_id]["data"]
        
        if node_data.type == "agent":
            # 执行Agent
            agent = self.agents[node_id]
            input_data = self._prepare_node_input(node_id)
            result = await agent.process(input_data)
            self.execution_context["results"][node_id] = result
            
        elif node_data.type == "condition":
            # 评估条件
            condition_result = await self._evaluate_condition(node_data.condition)
            self.execution_context["results"][node_id] = condition_result
            
        elif node_data.type == "parallel":
            # 并行执行
            await self._execute_parallel_branches(node_id)
            
        # 执行后继节点
        successors = list(self.graph.successors(node_id))
        tasks = []
        for successor in successors:
            # 检查是否满足执行条件
            if await self._can_execute_node(successor):
                task = asyncio.create_task(self._execute_node(successor))
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks)
```

### 4. 可视化编辑器集成

```typescript
// frontend/components/flow-editor/AgentFlowEditor.tsx
import React, { useState, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { AgentNode } from '../agent-nodes/AgentNode';
import { AgentNodePanel } from './AgentNodePanel';
import { WorkflowToolbar } from './WorkflowToolbar';

const nodeTypes = {
  agent: AgentNode,
};

interface AgentFlowEditorProps {
  onSave: (workflow: any) => void;
  initialWorkflow?: any;
}

export const AgentFlowEditor: React.FC<AgentFlowEditorProps> = ({
  onSave,
  initialWorkflow,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState(
    initialWorkflow?.nodes || []
  );
  const [edges, setEdges, onEdgesChange] = useEdgesState(
    initialWorkflow?.edges || []
  );
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
  }, []);

  const addAgentNode = useCallback((agentType: string) => {
    const newNode = {
      id: `agent_${Date.now()}`,
      type: 'agent',
      position: { x: 250, y: 250 },
      data: {
        label: `${agentType} Agent`,
        agentType,
        config: {
          model: 'gpt-4',
          temperature: 0.7,
          tools: [],
        },
      },
    };
    setNodes((nds) => nds.concat(newNode));
  }, [setNodes]);

  const updateNodeConfig = useCallback((nodeId: string, config: any) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, config } }
          : node
      )
    );
  }, [setNodes]);

  const handleSave = () => {
    const workflow = {
      nodes: nodes.map((node) => ({
        id: node.id,
        type: node.type,
        position: node.position,
        agent_config: node.data.config,
      })),
      edges: edges.map((edge) => ({
        from_node: edge.source,
        to_node: edge.target,
        condition: edge.data?.condition,
      })),
    };
    onSave(workflow);
  };

  return (
    <div className="h-screen flex">
      <div className="flex-1 relative">
        <WorkflowToolbar
          onAddAgent={addAgentNode}
          onSave={handleSave}
        />
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>
      {selectedNode && (
        <AgentNodePanel
          node={selectedNode}
          onUpdate={(config) => updateNodeConfig(selectedNode.id, config)}
          onClose={() => setSelectedNode(null)}
        />
      )}
    </div>
  );
};
```

### 5. Agent节点组件

```typescript
// frontend/components/agent-nodes/AgentNode.tsx
import React from 'react';
import { Handle, Position } from 'reactflow';
import { 
  UserCircle, 
  Eye, 
  CheckCircle, 
  Brain,
  Search,
  FileText
} from 'lucide-react';

const agentIcons = {
  coordinator: UserCircle,
  supervisor: Eye,
  validator: CheckCircle,
  analyzer: Brain,
  researcher: Search,
  worker: FileText,
};

export const AgentNode = ({ data, selected }) => {
  const Icon = agentIcons[data.agentType] || UserCircle;
  
  return (
    <div
      className={`
        px-4 py-2 shadow-md rounded-md bg-white border-2
        ${selected ? 'border-blue-500' : 'border-gray-200'}
      `}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-16 !bg-gray-400"
      />
      <div className="flex items-center gap-2">
        <Icon className="w-5 h-5 text-gray-600" />
        <div>
          <div className="text-sm font-medium">{data.label}</div>
          <div className="text-xs text-gray-500">
            {data.config?.model || 'gpt-4'}
          </div>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-16 !bg-gray-400"
      />
    </div>
  );
};
```

## 使用示例

### 1. 创建简单的分析工作流

```python
# examples/analysis_workflow.py
import asyncio
from backend.core.workflow import WorkflowEngine
from backend.core.agents import CoordinatorAgent, ResearcherAgent, AnalyzerAgent, ReporterAgent

async def create_analysis_workflow():
    # 定义工作流
    workflow_definition = {
        "name": "Market Analysis Workflow",
        "nodes": [
            {
                "id": "coordinator",
                "type": "agent",
                "agent_config": {
                    "name": "market_coordinator",
                    "role": "coordinator",
                    "model": "gpt-4"
                }
            },
            {
                "id": "researcher",
                "type": "agent",
                "agent_config": {
                    "name": "market_researcher",
                    "role": "researcher",
                    "model": "gpt-4",
                    "tools": ["web_search", "news_api", "financial_data"]
                }
            },
            {
                "id": "analyzer",
                "type": "agent",
                "agent_config": {
                    "name": "data_analyzer",
                    "role": "analyzer",
                    "model": "gpt-4",
                    "tools": ["data_analysis", "visualization"]
                }
            },
            {
                "id": "reporter",
                "type": "agent",
                "agent_config": {
                    "name": "report_writer",
                    "role": "reporter",
                    "model": "gpt-4",
                    "tools": ["document_generator"]
                }
            }
        ],
        "edges": [
            {"from_node": "coordinator", "to_node": "researcher"},
            {"from_node": "researcher", "to_node": "analyzer"},
            {"from_node": "analyzer", "to_node": "reporter"}
        ]
    }
    
    # 创建并执行工作流
    engine = WorkflowEngine()
    engine.load_workflow(workflow_definition)
    
    # 输入数据
    input_data = {
        "task": "Analyze the AI market trends for 2024",
        "requirements": {
            "focus_areas": ["GenAI", "Computer Vision", "NLP"],
            "report_format": "executive_summary"
        }
    }
    
    # 执行
    results = await engine.execute(input_data)
    return results

# 运行示例
if __name__ == "__main__":
    results = asyncio.run(create_analysis_workflow())
    print(f"Analysis completed: {results}")
```

### 2. 复杂的多Agent协作示例

```python
# examples/complex_collaboration.py
async def software_development_workflow():
    """软件开发工作流 - 包含需求分析、设计、编码、测试"""
    
    workflow = {
        "name": "Software Development Pipeline",
        "nodes": [
            # 协调者
            {"id": "pm", "type": "agent", "agent_config": {
                "name": "project_manager",
                "role": "coordinator",
                "system_prompt": "You are a project manager coordinating a software development team."
            }},
            
            # 需求分析师
            {"id": "ba", "type": "agent", "agent_config": {
                "name": "business_analyst",
                "role": "analyzer",
                "tools": ["requirement_analyzer"],
                "system_prompt": "You are a business analyst who creates detailed requirement documents."
            }},
            
            # 架构师
            {"id": "architect", "type": "agent", "agent_config": {
                "name": "software_architect",
                "role": "analyzer",
                "tools": ["diagram_generator", "tech_stack_advisor"],
                "system_prompt": "You are a software architect who designs system architecture."
            }},
            
            # 开发者组 (并行)
            {"id": "parallel_dev", "type": "parallel"},
            {"id": "backend_dev", "type": "agent", "agent_config": {
                "name": "backend_developer",
                "role": "worker",
                "tools": ["code_generator", "api_designer"],
            }},
            {"id": "frontend_dev", "type": "agent", "agent_config": {
                "name": "frontend_developer",
                "role": "worker",
                "tools": ["code_generator", "ui_designer"],
            }},
            
            # 汇合点
            {"id": "join_dev", "type": "join"},
            
            # 测试员
            {"id": "tester", "type": "agent", "agent_config": {
                "name": "qa_engineer",
                "role": "validator",
                "tools": ["test_generator", "test_runner"],
            }},
            
            # 监督者 (全程监督)
            {"id": "supervisor", "type": "agent", "agent_config": {
                "name": "tech_lead",
                "role": "supervisor",
                "system_prompt": "You supervise the entire development process and ensure quality."
            }}
        ],
        "edges": [
            {"from_node": "pm", "to_node": "ba"},
            {"from_node": "ba", "to_node": "architect"},
            {"from_node": "architect", "to_node": "parallel_dev"},
            {"from_node": "parallel_dev", "to_node": "backend_dev"},
            {"from_node": "parallel_dev", "to_node": "frontend_dev"},
            {"from_node": "backend_dev", "to_node": "join_dev"},
            {"from_node": "frontend_dev", "to_node": "join_dev"},
            {"from_node": "join_dev", "to_node": "tester"},
            # 监督者连接
            {"from_node": "pm", "to_node": "supervisor"},
            {"from_node": "supervisor", "to_node": "tester"}
        ]
    }
    
    # 执行工作流
    engine = WorkflowEngine()
    engine.load_workflow(workflow)
    
    results = await engine.execute({
        "project": "Build a task management API",
        "requirements": "RESTful API with user auth, task CRUD, and real-time updates"
    })
    
    return results
```

## API使用

### 1. 创建工作流

```bash
POST /api/workflows
Content-Type: application/json

{
  "name": "My Analysis Workflow",
  "description": "Analyze market data",
  "workflow_definition": {
    "nodes": [...],
    "edges": [...]
  }
}
```

### 2. 执行工作流

```bash
POST /api/workflows/{workflow_id}/execute
Content-Type: application/json

{
  "input": {
    "task": "Analyze Q4 2024 market trends",
    "data_source": "financial_reports"
  }
}
```

### 3. 监控执行状态

```bash
GET /api/executions/{execution_id}/status

# WebSocket订阅实时更新
WS /api/executions/{execution_id}/stream
```

## 配置说明

### 环境变量配置

```bash
# .env
# LLM配置
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GOOGLE_API_KEY=your_key

# 数据库配置
DATABASE_URL=postgresql://user:pass@localhost/multiagent
REDIS_URL=redis://localhost:6379

# 向量数据库
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_key

# MCP工具配置
MCP_SERVER_URL=http://localhost:3000
MCP_API_KEY=your_key

# 监控配置
ENABLE_MONITORING=true
PROMETHEUS_PORT=9090
```

### Agent配置模板

```yaml
# config/agents/researcher.yaml
name: research_agent
role: researcher
model: gpt-4
temperature: 0.7
max_tokens: 2000
tools:
  - web_search
  - arxiv_search
  - wikipedia
  - news_api
system_prompt: |
  You are an expert researcher skilled at finding and analyzing information.
  Always cite your sources and provide comprehensive analysis.
```

## 部署指南

### 生产环境部署

```bash
# 1. 构建Docker镜像
docker build -t multiagent-orchestration:latest .

# 2. 使用Docker Compose部署
docker-compose -f docker-compose.prod.yml up -d

# 3. 配置Nginx反向代理
sudo cp nginx/multiagent.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/multiagent.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 4. 设置SSL证书
sudo certbot --nginx -d your-domain.com
```

### 扩展部署

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multiagent-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: multiagent-backend
  template:
    metadata:
      labels:
        app: multiagent-backend
    spec:
      containers:
      - name: backend
        image: multiagent-orchestration:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: multiagent-secrets
              key: database-url
```

## 故障排除

### 常见问题

1. **Agent执行超时**
   ```python
   # 增加超时时间
   agent_config.timeout = 300  # 5分钟
   ```

2. **内存不足**
   ```yaml
   # docker-compose.yml
   services:
     backend:
       mem_limit: 4g
   ```

3. **工具调用失败**
   - 检查API密钥配置
   - 验证网络连接
   - 查看工具日志

## 下一步

- 查看[完整文档](./docs/README.md)
- 探索[更多示例](./examples/)
- 加入[社区讨论](https://github.com/your-org/discussions)
- 贡献代码[开发指南](./CONTRIBUTING.md)