from typing import Dict, Any, List
import json
from .base_agent import BaseAgent, AgentConfig, AgentOutput


class CoordinatorAgent(BaseAgent):
    """Coordinator agent responsible for task decomposition and delegation"""
    
    def __init__(self, config: AgentConfig):
        # Set coordinator-specific system prompt
        if not config.system_prompt:
            config.system_prompt = """You are a skilled coordinator responsible for:
1. Breaking down complex tasks into manageable subtasks
2. Assigning tasks to appropriate team members based on their expertise
3. Monitoring progress and adjusting plans as needed
4. Ensuring effective communication between team members

When decomposing tasks:
- Identify clear, actionable subtasks
- Consider dependencies between tasks
- Estimate complexity and required expertise
- Suggest appropriate agent types for each subtask

Respond in JSON format when decomposing tasks."""
        
        config.role = "coordinator"
        super().__init__(config)
        
        self.task_graph = {}
        self.team_assignments = {}
    
    async def process(self, task: Dict[str, Any]) -> AgentOutput:
        """Process a coordination task"""
        try:
            task_type = task.get("type", "coordinate")
            
            if task_type == "decompose":
                return await self._decompose_task(task)
            elif task_type == "assign":
                return await self._assign_tasks(task)
            elif task_type == "monitor":
                return await self._monitor_progress(task)
            else:
                return await self._coordinate_general(task)
                
        except Exception as e:
            self.logger.error(f"Error processing task: {str(e)}")
            return AgentOutput(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def _decompose_task(self, task: Dict[str, Any]) -> AgentOutput:
        """Decompose a complex task into subtasks"""
        description = task.get("description", "")
        requirements = task.get("requirements", {})
        
        prompt = f"""Decompose the following task into subtasks:

Task: {description}
Requirements: {json.dumps(requirements, indent=2)}

Create a detailed task decomposition with:
1. Clear subtasks with descriptions
2. Dependencies between tasks
3. Required agent roles for each subtask
4. Estimated complexity (simple/moderate/complex)

Respond with a JSON structure like:
{{
    "subtasks": [
        {{
            "id": "task_1",
            "name": "Task name",
            "description": "What needs to be done",
            "dependencies": [],
            "required_role": "worker/researcher/analyzer",
            "complexity": "simple/moderate/complex",
            "estimated_time": "5m/30m/2h"
        }}
    ],
    "execution_order": ["task_1", "task_2"],
    "parallel_groups": [["task_1", "task_2"]]
}}"""
        
        response = await self.think(prompt)
        
        try:
            # Parse the JSON response
            decomposition = json.loads(response)
            
            # Store in task graph
            task_id = task.get("id", "unknown")
            self.task_graph[task_id] = decomposition
            
            return AgentOutput(
                success=True,
                data=decomposition,
                metadata={"task_count": len(decomposition.get("subtasks", []))}
            )
            
        except json.JSONDecodeError:
            # If response is not valid JSON, try to extract structured data
            return AgentOutput(
                success=True,
                data={"raw_decomposition": response},
                metadata={"format": "text"}
            )
    
    async def _assign_tasks(self, task: Dict[str, Any]) -> AgentOutput:
        """Assign tasks to appropriate agents"""
        subtasks = task.get("subtasks", [])
        available_agents = task.get("available_agents", [])
        
        prompt = f"""Assign the following subtasks to available agents:

Subtasks:
{json.dumps(subtasks, indent=2)}

Available Agents:
{json.dumps(available_agents, indent=2)}

Consider:
- Agent roles and capabilities
- Current workload (if provided)
- Task complexity and requirements

Respond with assignments in JSON format:
{{
    "assignments": [
        {{
            "task_id": "task_1",
            "assigned_to": "agent_id",
            "reason": "Why this agent was chosen"
        }}
    ],
    "unassigned": []
}}"""
        
        response = await self.think(prompt)
        
        try:
            assignments = json.loads(response)
            
            # Store assignments
            for assignment in assignments.get("assignments", []):
                task_id = assignment["task_id"]
                agent_id = assignment["assigned_to"]
                self.team_assignments[task_id] = agent_id
            
            return AgentOutput(
                success=True,
                data=assignments,
                metadata={"assigned_count": len(assignments.get("assignments", []))}
            )
            
        except json.JSONDecodeError:
            return AgentOutput(
                success=False,
                data=None,
                error="Failed to parse assignments"
            )
    
    async def _monitor_progress(self, task: Dict[str, Any]) -> AgentOutput:
        """Monitor task execution progress"""
        execution_id = task.get("execution_id")
        status_updates = task.get("status_updates", [])
        
        prompt = f"""Analyze the progress of task execution:

Execution ID: {execution_id}
Status Updates:
{json.dumps(status_updates, indent=2)}

Provide:
1. Overall progress assessment
2. Any bottlenecks or issues
3. Recommendations for optimization
4. Next steps

Respond in JSON format."""
        
        response = await self.think(prompt)
        
        try:
            analysis = json.loads(response)
            
            return AgentOutput(
                success=True,
                data=analysis,
                metadata={"execution_id": execution_id}
            )
            
        except json.JSONDecodeError:
            return AgentOutput(
                success=True,
                data={"analysis": response},
                metadata={"format": "text"}
            )
    
    async def _coordinate_general(self, task: Dict[str, Any]) -> AgentOutput:
        """Handle general coordination tasks"""
        prompt = f"""As a coordinator, handle the following task:

{json.dumps(task, indent=2)}

Provide a structured response with your coordination plan."""
        
        response = await self.think(prompt)
        
        return AgentOutput(
            success=True,
            data={"coordination_plan": response}
        )