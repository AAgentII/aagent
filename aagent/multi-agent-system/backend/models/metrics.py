import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from core.base import BaseModel


class AgentMetric(BaseModel):
    """Agent performance metrics"""
    __tablename__ = "agent_metrics"
    
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id"))
    
    # Performance metrics
    execution_time = Column(Float)  # in seconds
    token_usage = Column(Integer)
    success_rate = Column(Float)  # 0-1
    error_count = Column(Integer, default=0)
    
    # Quality metrics
    quality_score = Column(Float)  # 0-1
    coherence_score = Column(Float)  # 0-1
    completeness_score = Column(Float)  # 0-1
    
    # Resource usage
    memory_usage_mb = Column(Float)
    cpu_usage_percent = Column(Float)
    
    # Timestamp
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    agent = relationship("Agent", back_populates="metrics")