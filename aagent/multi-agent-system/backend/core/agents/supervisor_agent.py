from typing import Dict, Any, List, Optional
import json
import asyncio
from datetime import datetime
from .base_agent import BaseAgent, AgentConfig, AgentOutput


class SupervisorAgent(BaseAgent):
    """Supervisor agent responsible for quality control and monitoring"""
    
    def __init__(self, config: AgentConfig):
        # Set supervisor-specific system prompt
        if not config.system_prompt:
            config.system_prompt = """You are a meticulous supervisor responsible for:
1. Monitoring the quality of work produced by other agents
2. Identifying potential issues or bottlenecks in execution
3. Providing constructive feedback and guidance
4. Ensuring standards and requirements are met
5. Intervening when necessary to correct course

When evaluating work:
- Check for completeness and accuracy
- Verify adherence to requirements
- Assess quality and coherence
- Identify areas for improvement

Provide structured feedback in JSON format when possible."""
        
        config.role = "supervisor"
        super().__init__(config)
        
        self.monitoring_tasks = {}
        self.quality_thresholds = {
            "min_quality_score": 0.7,
            "min_completeness": 0.8,
            "max_error_rate": 0.1
        }
    
    async def process(self, task: Dict[str, Any]) -> AgentOutput:
        """Process a supervision task"""
        try:
            task_type = task.get("type", "supervise")
            
            if task_type == "monitor":
                return await self._monitor_execution(task)
            elif task_type == "review":
                return await self._review_results(task)
            elif task_type == "intervene":
                return await self._intervene(task)
            elif task_type == "report":
                return await self._generate_report(task)
            else:
                return await self._supervise_general(task)
                
        except Exception as e:
            self.logger.error(f"Error processing supervision task: {str(e)}")
            return AgentOutput(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def _monitor_execution(self, task: Dict[str, Any]) -> AgentOutput:
        """Monitor ongoing task execution"""
        worker_id = task.get("worker_id")
        task_id = task.get("task_id")
        execution_data = task.get("execution_data", {})
        
        # Create monitoring record
        monitoring_id = f"{task_id}_{worker_id}"
        self.monitoring_tasks[monitoring_id] = {
            "worker_id": worker_id,
            "task_id": task_id,
            "start_time": datetime.now(),
            "checkpoints": [],
            "issues": []
        }
        
        prompt = f"""Monitor the execution of the following task:

Worker: {worker_id}
Task ID: {task_id}
Current Status: {json.dumps(execution_data, indent=2)}

Evaluate:
1. Progress towards completion
2. Quality of intermediate results
3. Any potential issues or risks
4. Need for intervention

Respond with a monitoring assessment in JSON format:
{{
    "progress_percentage": 0-100,
    "quality_assessment": {{
        "score": 0-1,
        "issues": [],
        "strengths": []
    }},
    "risks": [],
    "recommendations": [],
    "intervention_needed": true/false
}}"""
        
        response = await self.think(prompt)
        
        try:
            assessment = json.loads(response)
            
            # Store checkpoint
            self.monitoring_tasks[monitoring_id]["checkpoints"].append({
                "timestamp": datetime.now().isoformat(),
                "assessment": assessment
            })
            
            # Check if intervention is needed
            if assessment.get("intervention_needed", False):
                self.logger.warning(f"Intervention needed for task {task_id}")
                
            return AgentOutput(
                success=True,
                data=assessment,
                metadata={
                    "monitoring_id": monitoring_id,
                    "worker_id": worker_id
                }
            )
            
        except json.JSONDecodeError:
            return AgentOutput(
                success=True,
                data={"assessment": response},
                metadata={"format": "text"}
            )
    
    async def _review_results(self, task: Dict[str, Any]) -> AgentOutput:
        """Review completed work"""
        results = task.get("results", {})
        requirements = task.get("requirements", {})
        worker_id = task.get("worker_id")
        
        prompt = f"""Review the following completed work:

Results:
{json.dumps(results, indent=2)}

Original Requirements:
{json.dumps(requirements, indent=2)}

Worker: {worker_id}

Provide a comprehensive review including:
1. Completeness check (all requirements met?)
2. Quality assessment (accuracy, clarity, usefulness)
3. Adherence to standards
4. Areas of excellence
5. Areas for improvement

Respond with a structured review in JSON format:
{{
    "overall_score": 0-1,
    "completeness_score": 0-1,
    "quality_score": 0-1,
    "requirements_met": true/false,
    "detailed_feedback": {{
        "strengths": [],
        "weaknesses": [],
        "suggestions": []
    }},
    "approval_status": "approved/needs_revision/rejected"
}}"""
        
        response = await self.think(prompt)
        
        try:
            review = json.loads(response)
            
            # Check against quality thresholds
            quality_score = review.get("quality_score", 0)
            if quality_score < self.quality_thresholds["min_quality_score"]:
                review["approval_status"] = "needs_revision"
                self.logger.warning(f"Quality below threshold: {quality_score}")
            
            return AgentOutput(
                success=True,
                data=review,
                metadata={
                    "worker_id": worker_id,
                    "reviewed_at": datetime.now().isoformat()
                }
            )
            
        except json.JSONDecodeError:
            return AgentOutput(
                success=True,
                data={"review": response},
                metadata={"format": "text"}
            )
    
    async def _intervene(self, task: Dict[str, Any]) -> AgentOutput:
        """Intervene in task execution"""
        issue = task.get("issue", {})
        worker_id = task.get("worker_id")
        task_id = task.get("task_id")
        
        prompt = f"""An intervention is needed:

Issue: {json.dumps(issue, indent=2)}
Worker: {worker_id}
Task: {task_id}

Provide intervention guidance:
1. Root cause analysis
2. Corrective actions
3. Preventive measures
4. Revised instructions or approach

Respond with intervention plan in JSON format."""
        
        response = await self.think(prompt)
        
        try:
            intervention_plan = json.loads(response)
            
            # Send intervention message to worker
            await self.send_message(
                to_agent=worker_id,
                content={
                    "type": "intervention",
                    "plan": intervention_plan,
                    "task_id": task_id
                },
                message_type="intervention"
            )
            
            return AgentOutput(
                success=True,
                data=intervention_plan,
                metadata={
                    "intervention_sent_to": worker_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except json.JSONDecodeError:
            return AgentOutput(
                success=True,
                data={"intervention_guidance": response},
                metadata={"format": "text"}
            )
    
    async def _generate_report(self, task: Dict[str, Any]) -> AgentOutput:
        """Generate supervision report"""
        execution_id = task.get("execution_id")
        monitoring_data = task.get("monitoring_data", {})
        
        # Collect all monitoring records for this execution
        relevant_monitoring = {
            k: v for k, v in self.monitoring_tasks.items()
            if execution_id in k
        }
        
        prompt = f"""Generate a comprehensive supervision report:

Execution ID: {execution_id}
Monitoring Data: {json.dumps(monitoring_data, indent=2)}
Monitoring Records: {json.dumps(relevant_monitoring, indent=2)}

Include:
1. Executive summary
2. Performance metrics
3. Quality assessment
4. Issues encountered and resolutions
5. Recommendations for future improvements

Format as a structured report."""
        
        response = await self.think(prompt)
        
        return AgentOutput(
            success=True,
            data={
                "report": response,
                "execution_id": execution_id,
                "generated_at": datetime.now().isoformat()
            }
        )
    
    async def _supervise_general(self, task: Dict[str, Any]) -> AgentOutput:
        """Handle general supervision tasks"""
        prompt = f"""As a supervisor, handle the following task:

{json.dumps(task, indent=2)}

Provide appropriate supervision guidance or assessment."""
        
        response = await self.think(prompt)
        
        return AgentOutput(
            success=True,
            data={"supervision_response": response}
        )
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get summary of all monitoring activities"""
        return {
            "active_monitoring": len(self.monitoring_tasks),
            "quality_thresholds": self.quality_thresholds,
            "recent_issues": [
                task.get("issues", [])
                for task in self.monitoring_tasks.values()
                if task.get("issues")
            ]
        }