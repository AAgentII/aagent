import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from pydantic import BaseModel
import asyncio
import json

from core.database import get_db
from models import Workflow, WorkflowExecution, NodeExecution, ExecutionStatus, WorkflowStatus
from core.workflow.workflow_engine import WorkflowEngine
import structlog

router = APIRouter()
logger = structlog.get_logger()


# Request/Response models
class ExecutionRequest(BaseModel):
    workflow_id: str
    input_data: Dict[str, Any]


class ExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    status: ExecutionStatus
    input_data: Dict[str, Any]
    output_data: Dict[str, Any] = None
    error_message: str = None
    started_at: str
    completed_at: str = None
    
    class Config:
        from_attributes = True


class NodeExecutionResponse(BaseModel):
    id: str
    node_id: str
    node_type: str
    status: ExecutionStatus
    input_data: Dict[str, Any] = None
    output_data: Dict[str, Any] = None
    error_message: str = None
    started_at: str
    completed_at: str = None
    
    class Config:
        from_attributes = True


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, execution_id: str):
        await websocket.accept()
        if execution_id not in self.active_connections:
            self.active_connections[execution_id] = []
        self.active_connections[execution_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, execution_id: str):
        if execution_id in self.active_connections:
            self.active_connections[execution_id].remove(websocket)
            if not self.active_connections[execution_id]:
                del self.active_connections[execution_id]
    
    async def send_update(self, execution_id: str, message: dict):
        if execution_id in self.active_connections:
            for connection in self.active_connections[execution_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass


manager = ConnectionManager()


@router.post("/", response_model=ExecutionResponse)
async def execute_workflow(
    execution_request: ExecutionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute a workflow"""
    # Get workflow
    result = await db.execute(
        select(Workflow).where(Workflow.id == execution_request.workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    if workflow.status != WorkflowStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow is not active"
        )
    
    # Create workflow engine and execute
    engine = WorkflowEngine(db)
    engine.load_workflow(workflow.definition)
    
    # Execute in background
    asyncio.create_task(
        execute_workflow_async(
            engine,
            execution_request.workflow_id,
            execution_request.input_data,
            db
        )
    )
    
    # Return execution status
    return ExecutionResponse(
        id=engine.current_execution.id,
        workflow_id=execution_request.workflow_id,
        status=ExecutionStatus.PENDING,
        input_data=execution_request.input_data,
        started_at=engine.current_execution.started_at.isoformat()
    )


async def execute_workflow_async(
    engine: WorkflowEngine,
    workflow_id: str,
    input_data: Dict[str, Any],
    db: AsyncSession
):
    """Execute workflow asynchronously"""
    try:
        # Add workflow_id to input data
        input_data["workflow_id"] = workflow_id
        
        # Execute workflow
        results = await engine.execute(input_data)
        
        # Send completion update
        await manager.send_update(
            str(engine.current_execution.id),
            {
                "type": "execution_completed",
                "status": "completed",
                "results": results
            }
        )
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        
        # Send error update
        await manager.send_update(
            str(engine.current_execution.id),
            {
                "type": "execution_failed",
                "status": "failed",
                "error": str(e)
            }
        )


@router.get("/", response_model=List[ExecutionResponse])
async def list_executions(
    workflow_id: str = None,
    status: ExecutionStatus = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List workflow executions"""
    query = select(WorkflowExecution)
    
    if workflow_id:
        query = query.where(WorkflowExecution.workflow_id == workflow_id)
    if status:
        query = query.where(WorkflowExecution.status == status)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    executions = result.scalars().all()
    
    return [
        ExecutionResponse(
            id=str(e.id),
            workflow_id=str(e.workflow_id),
            status=e.status,
            input_data=e.input_data,
            output_data=e.output_data,
            error_message=e.error_message,
            started_at=e.started_at.isoformat() if e.started_at else None,
            completed_at=e.completed_at.isoformat() if e.completed_at else None
        )
        for e in executions
    ]


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get execution details"""
    result = await db.execute(
        select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    return ExecutionResponse(
        id=str(execution.id),
        workflow_id=str(execution.workflow_id),
        status=execution.status,
        input_data=execution.input_data,
        output_data=execution.output_data,
        error_message=execution.error_message,
        started_at=execution.started_at.isoformat() if execution.started_at else None,
        completed_at=execution.completed_at.isoformat() if execution.completed_at else None
    )


@router.get("/{execution_id}/nodes", response_model=List[NodeExecutionResponse])
async def get_node_executions(
    execution_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get node execution details"""
    result = await db.execute(
        select(NodeExecution).where(NodeExecution.workflow_execution_id == execution_id)
    )
    node_executions = result.scalars().all()
    
    return [
        NodeExecutionResponse(
            id=str(n.id),
            node_id=n.node_id,
            node_type=n.node_type,
            status=n.status,
            input_data=n.input_data,
            output_data=n.output_data,
            error_message=n.error_message,
            started_at=n.started_at.isoformat() if n.started_at else None,
            completed_at=n.completed_at.isoformat() if n.completed_at else None
        )
        for n in node_executions
    ]


@router.post("/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a running execution"""
    result = await db.execute(
        select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    if execution.status not in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Execution cannot be cancelled"
        )
    
    # Update status
    execution.status = ExecutionStatus.CANCELLED
    await db.commit()
    
    # Send cancellation update
    await manager.send_update(
        execution_id,
        {
            "type": "execution_cancelled",
            "status": "cancelled"
        }
    )
    
    return {"message": "Execution cancelled"}


@router.websocket("/{execution_id}/stream")
async def websocket_endpoint(
    websocket: WebSocket,
    execution_id: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time execution updates"""
    # Verify execution exists
    result = await db.execute(
        select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await manager.connect(websocket, execution_id)
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "connection_established",
            "execution_id": execution_id,
            "current_status": execution.status.value
        })
        
        # Keep connection alive
        while True:
            # Wait for messages (heartbeat)
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, execution_id)