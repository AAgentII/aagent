import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
import uuid

from core.database import get_db
from models import Agent, AgentRole
from core.agents import AgentConfig

router = APIRouter()


# Request/Response models
class AgentCreate(BaseModel):
    name: str
    role: AgentRole
    model: str = "claude-3-sonnet-20240229"
    temperature: float = 0.7
    max_tokens: int = 2000
    system_prompt: str = None
    tools: List[str] = []
    config: dict = {}


class AgentUpdate(BaseModel):
    name: str = None
    model: str = None
    temperature: float = None
    max_tokens: int = None
    system_prompt: str = None
    tools: List[str] = None
    config: dict = None
    is_active: bool = None


class AgentResponse(BaseModel):
    id: str
    name: str
    role: AgentRole
    model: str
    temperature: float
    max_tokens: int
    system_prompt: str = None
    tools: List[str]
    config: dict
    is_active: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.post("/", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new agent configuration"""
    # Check if agent with same name exists
    result = await db.execute(
        select(Agent).where(Agent.name == agent_data.name)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent with this name already exists"
        )
    
    agent = Agent(
        id=uuid.uuid4(),
        name=agent_data.name,
        role=agent_data.role,
        model=agent_data.model,
        temperature=agent_data.temperature,
        max_tokens=agent_data.max_tokens,
        system_prompt=agent_data.system_prompt,
        tools=agent_data.tools,
        config=agent_data.config,
        is_active=True
    )
    
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    
    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        role=agent.role,
        model=agent.model,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
        system_prompt=agent.system_prompt,
        tools=agent.tools,
        config=agent.config,
        is_active=agent.is_active,
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat()
    )


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    role: AgentRole = None,
    is_active: bool = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all agent configurations"""
    query = select(Agent)
    
    if role:
        query = query.where(Agent.role == role)
    if is_active is not None:
        query = query.where(Agent.is_active == is_active)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    agents = result.scalars().all()
    
    return [
        AgentResponse(
            id=str(a.id),
            name=a.name,
            role=a.role,
            model=a.model,
            temperature=a.temperature,
            max_tokens=a.max_tokens,
            system_prompt=a.system_prompt,
            tools=a.tools,
            config=a.config,
            is_active=a.is_active,
            created_at=a.created_at.isoformat(),
            updated_at=a.updated_at.isoformat()
        )
        for a in agents
    ]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific agent configuration"""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        role=agent.role,
        model=agent.model,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
        system_prompt=agent.system_prompt,
        tools=agent.tools,
        config=agent.config,
        is_active=agent.is_active,
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat()
    )


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_update: AgentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an agent configuration"""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Update fields
    if agent_update.name is not None:
        # Check if new name already exists
        result = await db.execute(
            select(Agent).where(
                Agent.name == agent_update.name,
                Agent.id != agent_id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent with this name already exists"
            )
        agent.name = agent_update.name
    
    if agent_update.model is not None:
        agent.model = agent_update.model
    if agent_update.temperature is not None:
        agent.temperature = agent_update.temperature
    if agent_update.max_tokens is not None:
        agent.max_tokens = agent_update.max_tokens
    if agent_update.system_prompt is not None:
        agent.system_prompt = agent_update.system_prompt
    if agent_update.tools is not None:
        agent.tools = agent_update.tools
    if agent_update.config is not None:
        agent.config = agent_update.config
    if agent_update.is_active is not None:
        agent.is_active = agent_update.is_active
    
    await db.commit()
    await db.refresh(agent)
    
    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        role=agent.role,
        model=agent.model,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
        system_prompt=agent.system_prompt,
        tools=agent.tools,
        config=agent.config,
        is_active=agent.is_active,
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat()
    )


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete an agent configuration"""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    await db.delete(agent)
    await db.commit()
    
    return {"message": "Agent deleted successfully"}


@router.get("/roles/available")
async def get_available_roles():
    """Get available agent roles"""
    return {
        "roles": [
            {
                "value": role.value,
                "name": role.name,
                "description": get_role_description(role)
            }
            for role in AgentRole
        ]
    }


@router.get("/models/available")
async def get_available_models():
    """Get available LLM models"""
    return {
        "models": [
            {
                "id": "claude-3-sonnet-20240229",
                "name": "Claude 3 Sonnet",
                "provider": "Anthropic",
                "context_window": 200000
            },
            {
                "id": "claude-3-opus-20240229",
                "name": "Claude 3 Opus",
                "provider": "Anthropic",
                "context_window": 200000
            },
            {
                "id": "gpt-4-turbo-preview",
                "name": "GPT-4 Turbo",
                "provider": "OpenAI",
                "context_window": 128000
            },
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "provider": "OpenAI",
                "context_window": 16000
            }
        ]
    }


@router.get("/tools/available")
async def get_available_tools():
    """Get available tools"""
    return {
        "tools": [
            {
                "id": "web_search",
                "name": "Web Search",
                "description": "Search the web for information"
            },
            {
                "id": "code_executor",
                "name": "Code Executor",
                "description": "Execute code in a sandboxed environment"
            },
            {
                "id": "data_analyzer",
                "name": "Data Analyzer",
                "description": "Analyze and visualize data"
            },
            {
                "id": "file_reader",
                "name": "File Reader",
                "description": "Read and parse various file formats"
            },
            {
                "id": "api_caller",
                "name": "API Caller",
                "description": "Make HTTP API calls"
            }
        ]
    }


def get_role_description(role: AgentRole) -> str:
    """Get description for agent role"""
    descriptions = {
        AgentRole.COORDINATOR: "Coordinates tasks and manages workflow execution",
        AgentRole.SUPERVISOR: "Monitors execution and ensures quality",
        AgentRole.WORKER: "Executes assigned tasks",
        AgentRole.VALIDATOR: "Validates results and ensures compliance",
        AgentRole.RESEARCHER: "Conducts research and gathers information",
        AgentRole.ANALYZER: "Analyzes data and provides insights"
    }
    return descriptions.get(role, "")