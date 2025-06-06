from typing import Dict, Any, List
import json
from datetime import datetime
from .base_agent import BaseAgent, AgentConfig, AgentOutput


class WorkerAgent(BaseAgent):
    """Worker agent responsible for executing specific tasks"""
    
    def __init__(self, config: AgentConfig):
        # Set worker-specific system prompt
        if not config.system_prompt:
            config.system_prompt = """You are a diligent worker agent responsible for:
1. Executing assigned tasks with precision and attention to detail
2. Following instructions and requirements carefully
3. Producing high-quality outputs
4. Reporting progress and any issues encountered
5. Collaborating with other agents when needed

When executing tasks:
- Understand the requirements thoroughly before starting
- Break down complex work into manageable steps
- Verify your output meets all requirements
- Document your process and decisions
- Ask for clarification if instructions are unclear"""
        
        config.role = "worker"
        super().__init__(config)
        
        self.current_task = None
        self.task_history = []
    
    async def process(self, task: Dict[str, Any]) -> AgentOutput:
        """Process a work task"""
        try:
            self.current_task = task
            task_type = task.get("type", "execute")
            
            if task_type == "execute":
                return await self._execute_task(task)
            elif task_type == "research":
                return await self._research_task(task)
            elif task_type == "analyze":
                return await self._analyze_task(task)
            elif task_type == "create":
                return await self._create_content(task)
            elif task_type == "code":
                return await self._write_code(task)
            else:
                return await self._execute_general(task)
                
        except Exception as e:
            self.logger.error(f"Error processing work task: {str(e)}")
            return AgentOutput(
                success=False,
                data=None,
                error=str(e)
            )
        finally:
            # Record task in history
            if self.current_task:
                self.task_history.append({
                    "task": self.current_task,
                    "completed_at": datetime.now().isoformat()
                })
            self.current_task = None
    
    async def _execute_task(self, task: Dict[str, Any]) -> AgentOutput:
        """Execute a general task"""
        description = task.get("description", "")
        requirements = task.get("requirements", {})
        
        prompt = f"""Execute the following task:

Task Description: {description}
Requirements: {json.dumps(requirements, indent=2)}

Provide a comprehensive solution that:
1. Addresses all requirements
2. Is well-structured and clear
3. Includes any necessary explanations
4. Highlights any assumptions made

Complete the task thoroughly and professionally."""
        
        response = await self.think(prompt)
        
        # Report progress
        await self.send_message(
            to_agent=task.get("supervisor_id", "supervisor"),
            content={
                "type": "progress",
                "task_id": task.get("id"),
                "status": "completed",
                "result_preview": response[:200] + "..."
            },
            message_type="progress"
        )
        
        return AgentOutput(
            success=True,
            data={
                "result": response,
                "task_id": task.get("id"),
                "completed_at": datetime.now().isoformat()
            }
        )
    
    async def _research_task(self, task: Dict[str, Any]) -> AgentOutput:
        """Execute a research task"""
        topic = task.get("topic", "")
        questions = task.get("questions", [])
        sources = task.get("sources", [])
        
        prompt = f"""Conduct research on the following:

Topic: {topic}
Key Questions: {json.dumps(questions, indent=2)}
Suggested Sources: {json.dumps(sources, indent=2)}

Provide:
1. Comprehensive findings
2. Answer to each question
3. Key insights discovered
4. Sources and references
5. Areas requiring further investigation

Format your research in a clear, structured manner."""
        
        response = await self.think(prompt)
        
        # If tools are available, use them
        research_data = {"findings": response}
        
        if "web_search" in self.tools:
            # Perform web searches for each question
            search_results = []
            for question in questions[:3]:  # Limit to 3 searches
                try:
                    results = await self.call_tool("web_search", query=question)
                    search_results.append({
                        "question": question,
                        "results": results
                    })
                except:
                    pass
            
            if search_results:
                research_data["search_results"] = search_results
        
        return AgentOutput(
            success=True,
            data=research_data,
            metadata={
                "topic": topic,
                "questions_count": len(questions)
            }
        )
    
    async def _analyze_task(self, task: Dict[str, Any]) -> AgentOutput:
        """Execute an analysis task"""
        data = task.get("data", {})
        analysis_type = task.get("analysis_type", "general")
        criteria = task.get("criteria", {})
        
        prompt = f"""Perform {analysis_type} analysis on the following data:

Data: {json.dumps(data, indent=2)}
Analysis Criteria: {json.dumps(criteria, indent=2)}

Provide:
1. Key findings and patterns
2. Statistical insights (if applicable)
3. Trends and correlations
4. Anomalies or outliers
5. Conclusions and recommendations

Present your analysis in a structured format with clear sections."""
        
        response = await self.think(prompt)
        
        analysis_result = {
            "analysis": response,
            "type": analysis_type,
            "timestamp": datetime.now().isoformat()
        }
        
        # If data analysis tools are available, use them
        if "data_analyzer" in self.tools and isinstance(data, (list, dict)):
            try:
                tool_analysis = await self.call_tool("data_analyzer", data=data)
                analysis_result["tool_analysis"] = tool_analysis
            except:
                pass
        
        return AgentOutput(
            success=True,
            data=analysis_result
        )
    
    async def _create_content(self, task: Dict[str, Any]) -> AgentOutput:
        """Create content based on requirements"""
        content_type = task.get("content_type", "general")
        topic = task.get("topic", "")
        guidelines = task.get("guidelines", {})
        target_audience = task.get("target_audience", "general")
        
        prompt = f"""Create {content_type} content on the following:

Topic: {topic}
Target Audience: {target_audience}
Guidelines: {json.dumps(guidelines, indent=2)}

Ensure the content is:
1. Appropriate for the target audience
2. Well-structured and engaging
3. Factually accurate
4. Following all provided guidelines
5. Original and creative

Create professional content that meets all requirements."""
        
        response = await self.think(prompt)
        
        return AgentOutput(
            success=True,
            data={
                "content": response,
                "type": content_type,
                "metadata": {
                    "topic": topic,
                    "audience": target_audience,
                    "word_count": len(response.split())
                }
            }
        )
    
    async def _write_code(self, task: Dict[str, Any]) -> AgentOutput:
        """Write code based on specifications"""
        language = task.get("language", "python")
        requirements = task.get("requirements", {})
        specifications = task.get("specifications", "")
        
        prompt = f"""Write {language} code for the following:

Specifications: {specifications}
Requirements: {json.dumps(requirements, indent=2)}

Ensure the code:
1. Follows best practices for {language}
2. Is well-commented and documented
3. Handles errors appropriately
4. Is efficient and maintainable
5. Includes example usage if applicable

Provide complete, working code."""
        
        response = await self.think(prompt)
        
        code_result = {
            "code": response,
            "language": language,
            "timestamp": datetime.now().isoformat()
        }
        
        # If code execution tools are available, test the code
        if "code_executor" in self.tools and language == "python":
            try:
                execution_result = await self.call_tool(
                    "code_executor",
                    code=response,
                    language=language
                )
                code_result["execution_result"] = execution_result
            except Exception as e:
                code_result["execution_error"] = str(e)
        
        return AgentOutput(
            success=True,
            data=code_result
        )
    
    async def _execute_general(self, task: Dict[str, Any]) -> AgentOutput:
        """Execute a general task"""
        prompt = f"""As a worker agent, execute the following task:

{json.dumps(task, indent=2)}

Complete the task thoroughly and provide comprehensive results."""
        
        response = await self.think(prompt)
        
        return AgentOutput(
            success=True,
            data={
                "result": response,
                "task_type": "general"
            }
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get worker performance metrics"""
        completed_tasks = len(self.task_history)
        
        return {
            "completed_tasks": completed_tasks,
            "current_task": self.current_task.get("id") if self.current_task else None,
            "average_completion_time": self._calculate_avg_completion_time(),
            "task_types": self._get_task_type_distribution()
        }
    
    def _calculate_avg_completion_time(self) -> float:
        """Calculate average task completion time"""
        # Simplified calculation for now
        return 0.0
    
    def _get_task_type_distribution(self) -> Dict[str, int]:
        """Get distribution of task types completed"""
        distribution = {}
        for task_record in self.task_history:
            task_type = task_record["task"].get("type", "unknown")
            distribution[task_type] = distribution.get(task_type, 0) + 1
        return distribution