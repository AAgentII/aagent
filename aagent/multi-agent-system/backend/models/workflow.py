import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import Column, String, JSON, ForeignKey, Enum as SQLEnum, Integer, Boolean, Text, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from core.base import BaseModel


class WorkflowStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ExecutionStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRole(enum.Enum):
    COORDINATOR = "coordinator"
    SUPERVISOR = "supervisor"
    WORKER = "worker"
    VALIDATOR = "validator"
    RESEARCHER = "researcher"
    ANALYZER = "analyzer"


class Workflow(BaseModel):
    """Workflow definition model"""
    __tablename__ = "workflows"
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.DRAFT, nullable=False)
    definition = Column(JSON, nullable=False)  # Stores nodes and edges
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    executions = relationship("WorkflowExecution", back_populates="workflow")
    creator = relationship("User", back_populates="workflows")


class WorkflowExecution(BaseModel):
    """Workflow execution instance"""
    __tablename__ = "workflow_executions"
    
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    status = Column(SQLEnum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False)
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    node_executions = relationship("NodeExecution", back_populates="workflow_execution")


class NodeExecution(BaseModel):
    """Individual node execution within a workflow"""
    __tablename__ = "node_executions"
    
    workflow_execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id"), nullable=False)
    node_id = Column(String(255), nullable=False)
    node_type = Column(String(50), nullable=False)
    status = Column(SQLEnum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False)
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    workflow_execution = relationship("WorkflowExecution", back_populates="node_executions")


class Agent(BaseModel):
    """Agent configuration model"""
    __tablename__ = "agents"
    
    name = Column(String(255), nullable=False, unique=True)
    role = Column(SQLEnum(AgentRole), nullable=False)
    model = Column(String(100), default="claude-3-sonnet")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2000)
    system_prompt = Column(Text)
    tools = Column(JSON, default=list)  # List of tool names
    config = Column(JSON, default=dict)  # Additional configuration
    is_active = Column(Boolean, default=True)
    
    # Relationships
    metrics = relationship("AgentMetric", back_populates="agent")