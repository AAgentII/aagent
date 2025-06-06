from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json
import uuid
from anthropic import AsyncAnthropic
from config.settings import settings
import structlog

logger = structlog.get_logger()


@dataclass
class AgentConfig:
    """Agent configuration"""
    name: str
    role: str
    model: str = "claude-3-sonnet-20240229"
    temperature: float = 0.7
    max_tokens: int = 2000
    system_prompt: Optional[str] = None
    tools: List[str] = None
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = []


@dataclass
class AgentMessage:
    """Message between agents"""
    id: str
    from_agent: str
    to_agent: str
    content: Any
    timestamp: datetime
    message_type: str = "task"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "message_type": self.message_type
        }


@dataclass
class AgentOutput:
    """Agent execution output"""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.id = f"{config.role}_{config.name}_{uuid.uuid4().hex[:8]}"
        self.message_queue = asyncio.Queue()
        self.memory = []
        self.tools = self._load_tools(config.tools)
        
        # Initialize Claude client
        self.claude_client = AsyncAnthropic(
            api_key=settings.claude_api_key,
            base_url=settings.claude_api_base_url
        )
        
        self.logger = logger.bind(agent_id=self.id, agent_role=config.role)
    
    def _load_tools(self, tool_names: List[str]) -> Dict[str, Any]:
        """Load tools for the agent"""
        tools = {}
        # Tool loading implementation will be added later
        return tools
    
    @abstractmethod
    async def process(self, task: Dict[str, Any]) -> AgentOutput:
        """Process a task - must be implemented by subclasses"""
        pass
    
    async def think(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Use LLM to think about a problem"""
        try:
            messages = []
            
            # Add system prompt if configured
            if self.config.system_prompt:
                messages.append({
                    "role": "system",
                    "content": self.config.system_prompt
                })
            
            # Add context from memory if available
            if self.memory:
                recent_memory = self.memory[-5:]  # Last 5 interactions
                memory_context = "\n".join([
                    f"Previous: {mem['input']}\nResponse: {mem['output']}"
                    for mem in recent_memory
                ])
                messages.append({
                    "role": "system",
                    "content": f"Recent context:\n{memory_context}"
                })
            
            # Add the main prompt
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Call Claude API
            response = await self.claude_client.messages.create(
                model=self.config.model,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            result = response.content[0].text
            
            # Store in memory
            self.memory.append({
                "timestamp": datetime.now(),
                "input": prompt,
                "output": result
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in thinking: {str(e)}")
            raise
    
    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """Call a tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not available for this agent")
        
        tool = self.tools[tool_name]
        return await tool(**kwargs)
    
    async def receive_message(self, message: AgentMessage):
        """Receive a message from another agent"""
        await self.message_queue.put(message)
        self.logger.info(f"Received message from {message.from_agent}")
    
    async def send_message(self, to_agent: str, content: Any, message_type: str = "task"):
        """Send a message to another agent"""
        message = AgentMessage(
            id=str(uuid.uuid4()),
            from_agent=self.id,
            to_agent=to_agent,
            content=content,
            timestamp=datetime.now(),
            message_type=message_type
        )
        
        # In a real implementation, this would use a message bus
        # For now, we'll just log it
        self.logger.info(f"Sending message to {to_agent}: {message_type}")
        
        return message
    
    async def wait_for_message(self, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """Wait for a message"""
        try:
            if timeout:
                return await asyncio.wait_for(self.message_queue.get(), timeout)
            else:
                return await self.message_queue.get()
        except asyncio.TimeoutError:
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "id": self.id,
            "name": self.config.name,
            "role": self.config.role,
            "queue_size": self.message_queue.qsize(),
            "memory_size": len(self.memory),
            "tools": list(self.tools.keys())
        }