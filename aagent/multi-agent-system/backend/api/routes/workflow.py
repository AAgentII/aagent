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
from models import Workflow, WorkflowStatus
from core.workflow.workflow_engine import WorkflowEngine

router = APIRouter()


# Request/Response models
class WorkflowCreate(BaseModel):
    name: str
    description: str
    definition: dict


class WorkflowUpdate(BaseModel):
    name: str = None
    description: str = None
    definition: dict = None
    status: WorkflowStatus = None


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    status: WorkflowStatus
    definition: dict
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new workflow"""
    workflow = Workflow(
        id=uuid.uuid4(),
        name=workflow_data.name,
        description=workflow_data.description,
        definition=workflow_data.definition,
        status=WorkflowStatus.DRAFT
    )
    
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    
    return WorkflowResponse(
        id=str(workflow.id),
        name=workflow.name,
        description=workflow.description,
        status=workflow.status,
        definition=workflow.definition,
        created_at=workflow.created_at.isoformat(),
        updated_at=workflow.updated_at.isoformat()
    )


@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all workflows"""
    result = await db.execute(
        select(Workflow).offset(skip).limit(limit)
    )
    workflows = result.scalars().all()
    
    return [
        WorkflowResponse(
            id=str(w.id),
            name=w.name,
            description=w.description,
            status=w.status,
            definition=w.definition,
            created_at=w.created_at.isoformat(),
            updated_at=w.updated_at.isoformat()
        )
        for w in workflows
    ]


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific workflow"""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    return WorkflowResponse(
        id=str(workflow.id),
        name=workflow.name,
        description=workflow.description,
        status=workflow.status,
        definition=workflow.definition,
        created_at=workflow.created_at.isoformat(),
        updated_at=workflow.updated_at.isoformat()
    )


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    workflow_update: WorkflowUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a workflow"""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Update fields
    if workflow_update.name is not None:
        workflow.name = workflow_update.name
    if workflow_update.description is not None:
        workflow.description = workflow_update.description
    if workflow_update.definition is not None:
        workflow.definition = workflow_update.definition
    if workflow_update.status is not None:
        workflow.status = workflow_update.status
    
    await db.commit()
    await db.refresh(workflow)
    
    return WorkflowResponse(
        id=str(workflow.id),
        name=workflow.name,
        description=workflow.description,
        status=workflow.status,
        definition=workflow.definition,
        created_at=workflow.created_at.isoformat(),
        updated_at=workflow.updated_at.isoformat()
    )


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a workflow"""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    await db.delete(workflow)
    await db.commit()
    
    return {"message": "Workflow deleted successfully"}


@router.post("/{workflow_id}/validate")
async def validate_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Validate a workflow definition"""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Validate workflow structure
    try:
        engine = WorkflowEngine(db)
        engine.load_workflow(workflow.definition)
        
        # Basic validation checks
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check for start nodes
        nodes = workflow.definition.get("nodes", [])
        if not nodes:
            validation_results["valid"] = False
            validation_results["errors"].append("No nodes defined in workflow")
        
        # Check for agent nodes
        agent_nodes = [n for n in nodes if n.get("type") == "agent"]
        if not agent_nodes:
            validation_results["warnings"].append("No agent nodes found in workflow")
        
        return validation_results
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [str(e)],
            "warnings": []
        }