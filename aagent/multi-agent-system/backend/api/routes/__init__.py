import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.workflow import router as workflow_router
from core.agent import router as agent_router
from core.execution import router as execution_router
from core.health import router as health_router

__all__ = [
    "workflow_router",
    "agent_router",
    "execution_router",
    "health_router"
]