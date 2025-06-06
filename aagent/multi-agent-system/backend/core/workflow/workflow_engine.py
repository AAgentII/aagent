from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import asyncio
import uuid
import json
import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession

from models import WorkflowExecution, NodeExecution, ExecutionStatus
from core.agents import BaseAgent, AgentConfig, CoordinatorAgent, SupervisorAgent, WorkerAgent, ValidatorAgent
import structlog

logger = structlog.get_logger()


@dataclass
class WorkflowNode:
    """Workflow node definition"""
    id: str
    type: str  # agent, start, end, condition, parallel, join
    config: Dict[str, Any]
    agent_config: Optional[AgentConfig] = None


@dataclass
class WorkflowEdge:
    """Workflow edge definition"""
    from_node: str
    to_node: str
    condition: Optional[str] = None


class WorkflowEngine:
    """Core workflow execution engine"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.graph = nx.DiGraph()
        self.agents: Dict[str, BaseAgent] = {}
        self.execution_context: Dict[str, Any] = {}
        self.current_execution: Optional[WorkflowExecution] = None
        self.logger = logger.bind(component="workflow_engine")
    
    def load_workflow(self, workflow_definition: Dict[str, Any]):
        """Load workflow definition into the engine"""
        # Clear existing graph
        self.graph.clear()
        self.agents.clear()
        
        # Load nodes
        for node_data in workflow_definition.get("nodes", []):
            node = WorkflowNode(
                id=node_data["id"],
                type=node_data["type"],
                config=node_data.get("config", {}),
                agent_config=self._parse_agent_config(node_data.get("agent_config"))
            )
            
            self.graph.add_node(node.id, data=node)
            
            # Create agent if it's an agent node
            if node.type == "agent" and node.agent_config:
                agent = self._create_agent(node.agent_config)
                self.agents[node.id] = agent
        
        # Load edges
        for edge_data in workflow_definition.get("edges", []):
            edge = WorkflowEdge(
                from_node=edge_data["from_node"],
                to_node=edge_data["to_node"],
                condition=edge_data.get("condition")
            )
            
            self.graph.add_edge(
                edge.from_node,
                edge.to_node,
                condition=edge.condition
            )
    
    def _parse_agent_config(self, config_data: Optional[Dict]) -> Optional[AgentConfig]:
        """Parse agent configuration"""
        if not config_data:
            return None
        
        return AgentConfig(
            name=config_data.get("name", "unnamed"),
            role=config_data.get("role", "worker"),
            model=config_data.get("model", "claude-3-sonnet-20240229"),
            temperature=config_data.get("temperature", 0.7),
            max_tokens=config_data.get("max_tokens", 2000),
            system_prompt=config_data.get("system_prompt"),
            tools=config_data.get("tools", [])
        )
    
    def _create_agent(self, config: AgentConfig) -> BaseAgent:
        """Create agent instance based on role"""
        agent_classes = {
            "coordinator": CoordinatorAgent,
            "supervisor": SupervisorAgent,
            "worker": WorkerAgent,
            "validator": ValidatorAgent
        }
        
        agent_class = agent_classes.get(config.role, WorkerAgent)
        return agent_class(config)
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow"""
        execution_id = str(uuid.uuid4())
        self.logger.info(f"Starting workflow execution: {execution_id}")
        
        # Create execution record
        self.current_execution = WorkflowExecution(
            id=execution_id,
            workflow_id=input_data.get("workflow_id"),
            status=ExecutionStatus.RUNNING,
            input_data=input_data,
            started_at=datetime.utcnow()
        )
        self.db_session.add(self.current_execution)
        await self.db_session.commit()
        
        # Initialize execution context
        self.execution_context = {
            "execution_id": execution_id,
            "input": input_data,
            "results": {},
            "variables": {}
        }
        
        try:
            # Find start nodes
            start_nodes = self._find_start_nodes()
            
            # Execute workflow
            await self._execute_nodes(start_nodes)
            
            # Update execution status
            self.current_execution.status = ExecutionStatus.COMPLETED
            self.current_execution.output_data = self.execution_context["results"]
            self.current_execution.completed_at = datetime.utcnow()
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {str(e)}")
            self.current_execution.status = ExecutionStatus.FAILED
            self.current_execution.error_message = str(e)
            self.current_execution.completed_at = datetime.utcnow()
            raise
        
        finally:
            await self.db_session.commit()
        
        return self.execution_context["results"]
    
    def _find_start_nodes(self) -> List[str]:
        """Find nodes with no incoming edges or explicit start nodes"""
        start_nodes = []
        
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]["data"]
            
            # Explicit start node
            if node_data.type == "start":
                start_nodes.append(node_id)
            # No incoming edges
            elif self.graph.in_degree(node_id) == 0:
                start_nodes.append(node_id)
        
        return start_nodes
    
    async def _execute_nodes(self, node_ids: List[str]):
        """Execute a list of nodes"""
        tasks = []
        
        for node_id in node_ids:
            task = asyncio.create_task(self._execute_node(node_id))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    async def _execute_node(self, node_id: str):
        """Execute a single node"""
        node_data = self.graph.nodes[node_id]["data"]
        self.logger.info(f"Executing node: {node_id} (type: {node_data.type})")
        
        # Create node execution record
        node_execution = NodeExecution(
            workflow_execution_id=self.current_execution.id,
            node_id=node_id,
            node_type=node_data.type,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        self.db_session.add(node_execution)
        await self.db_session.commit()
        
        try:
            # Execute based on node type
            if node_data.type == "agent":
                result = await self._execute_agent_node(node_id, node_data)
            elif node_data.type == "condition":
                result = await self._execute_condition_node(node_id, node_data)
            elif node_data.type == "parallel":
                result = await self._execute_parallel_node(node_id, node_data)
            elif node_data.type == "join":
                result = await self._execute_join_node(node_id, node_data)
            else:
                result = {"status": "completed"}
            
            # Store result
            self.execution_context["results"][node_id] = result
            
            # Update node execution
            node_execution.status = ExecutionStatus.COMPLETED
            node_execution.output_data = result
            node_execution.completed_at = datetime.utcnow()
            
            # Execute successor nodes
            await self._execute_successors(node_id)
            
        except Exception as e:
            self.logger.error(f"Node execution failed: {node_id} - {str(e)}")
            node_execution.status = ExecutionStatus.FAILED
            node_execution.error_message = str(e)
            node_execution.completed_at = datetime.utcnow()
            raise
        
        finally:
            await self.db_session.commit()
    
    async def _execute_agent_node(self, node_id: str, node_data: WorkflowNode) -> Dict[str, Any]:
        """Execute an agent node"""
        agent = self.agents.get(node_id)
        if not agent:
            raise ValueError(f"Agent not found for node: {node_id}")
        
        # Prepare input for agent
        agent_input = self._prepare_agent_input(node_id)
        
        # Execute agent
        output = await agent.process(agent_input)
        
        return {
            "success": output.success,
            "data": output.data,
            "error": output.error,
            "metadata": output.metadata
        }
    
    async def _execute_condition_node(self, node_id: str, node_data: WorkflowNode) -> Dict[str, Any]:
        """Execute a condition node"""
        condition = node_data.config.get("condition", "")
        
        # Evaluate condition using context
        try:
            # Simple evaluation - in production, use safe evaluation
            result = eval(condition, {"context": self.execution_context})
            return {"result": result}
        except Exception as e:
            self.logger.error(f"Condition evaluation failed: {str(e)}")
            return {"result": False, "error": str(e)}
    
    async def _execute_parallel_node(self, node_id: str, node_data: WorkflowNode) -> Dict[str, Any]:
        """Execute parallel branches"""
        # Get all successor nodes
        successors = list(self.graph.successors(node_id))
        
        # Execute all successors in parallel
        await self._execute_nodes(successors)
        
        return {"parallel_branches": len(successors)}
    
    async def _execute_join_node(self, node_id: str, node_data: WorkflowNode) -> Dict[str, Any]:
        """Wait for all incoming branches to complete"""
        predecessors = list(self.graph.predecessors(node_id))
        
        # Check if all predecessors have completed
        all_completed = all(
            pred_id in self.execution_context["results"]
            for pred_id in predecessors
        )
        
        if not all_completed:
            # Wait a bit and check again
            await asyncio.sleep(1)
            return await self._execute_join_node(node_id, node_data)
        
        return {"joined_branches": len(predecessors)}
    
    async def _execute_successors(self, node_id: str):
        """Execute successor nodes"""
        successors = list(self.graph.successors(node_id))
        
        # Filter successors based on conditions
        valid_successors = []
        for successor_id in successors:
            edge_data = self.graph.edges[node_id, successor_id]
            condition = edge_data.get("condition")
            
            if condition:
                # Evaluate edge condition
                try:
                    if eval(condition, {"context": self.execution_context}):
                        valid_successors.append(successor_id)
                except:
                    self.logger.error(f"Edge condition evaluation failed: {condition}")
            else:
                valid_successors.append(successor_id)
        
        # Execute valid successors
        if valid_successors:
            await self._execute_nodes(valid_successors)
    
    def _prepare_agent_input(self, node_id: str) -> Dict[str, Any]:
        """Prepare input data for an agent"""
        # Get inputs from predecessor nodes
        predecessors = list(self.graph.predecessors(node_id))
        
        inputs = {}
        for pred_id in predecessors:
            if pred_id in self.execution_context["results"]:
                inputs[pred_id] = self.execution_context["results"][pred_id]
        
        # Add global context
        return {
            "node_id": node_id,
            "inputs": inputs,
            "context": self.execution_context.get("input", {}),
            "variables": self.execution_context.get("variables", {})
        }
    
    def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status"""
        if not self.current_execution:
            return {"status": "not_started"}
        
        return {
            "execution_id": str(self.current_execution.id),
            "status": self.current_execution.status.value,
            "started_at": self.current_execution.started_at.isoformat() if self.current_execution.started_at else None,
            "completed_at": self.current_execution.completed_at.isoformat() if self.current_execution.completed_at else None,
            "progress": self._calculate_progress()
        }
    
    def _calculate_progress(self) -> float:
        """Calculate execution progress"""
        total_nodes = len(self.graph.nodes())
        completed_nodes = len(self.execution_context.get("results", {}))
        
        return completed_nodes / total_nodes if total_nodes > 0 else 0.0