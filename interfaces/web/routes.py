"""
API Routes for AMOS Web Interface
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from pydantic import BaseModel


router = APIRouter()


# Pydantic models
class CitizenCreate(BaseModel):
    name: str
    email: Optional[str] = None
    role_id: Optional[str] = None


class CitizenResponse(BaseModel):
    id: str
    name: str
    email: Optional[str]
    role_id: Optional[str]
    created_at: str


class TaskResponse(BaseModel):
    id: str
    type: str
    status: str
    agent_id: Optional[str]
    created_at: str


class InstitutionResponse(BaseModel):
    id: str
    name: str
    type: str
    head: Optional[str]
    status: str


# Mock data (replace with actual database calls)
citizens_db = []
tasks_db = []
institutions_db = []


@router.get("/citizens", response_model=List[CitizenResponse])
async def list_citizens():
    """List all citizens"""
    return citizens_db


@router.post("/citizens", response_model=CitizenResponse, status_code=status.HTTP_201_CREATED)
async def create_citizen(citizen: CitizenCreate):
    """Create a new citizen"""
    # In production, this would call the citizen registry
    new_citizen = {
        "id": f"CIT-{len(citizens_db) + 1:03d}",
        **citizen.dict(),
        "created_at": "2024-01-15T00:00:00Z"
    }
    citizens_db.append(new_citizen)
    return new_citizen


@router.get("/citizens/{citizen_id}", response_model=CitizenResponse)
async def get_citizen(citizen_id: str):
    """Get citizen by ID"""
    for citizen in citizens_db:
        if citizen["id"] == citizen_id:
            return citizen
    raise HTTPException(status_code=404, detail="Citizen not found")


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(status_filter: Optional[str] = None):
    """List all tasks with optional status filter"""
    if status_filter:
        return [t for t in tasks_db if t["status"] == status_filter]
    return tasks_db


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get task by ID"""
    for task in tasks_db:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")


@router.get("/institutions", response_model=List[InstitutionResponse])
async def list_institutions(type_filter: Optional[str] = None):
    """List all institutions with optional type filter"""
    if type_filter:
        return [i for i in institutions_db if i["type"] == type_filter]
    return institutions_db


@router.get("/institutions/{institution_id}", response_model=InstitutionResponse)
async def get_institution(institution_id: str):
    """Get institution by ID"""
    for institution in institutions_db:
        if institution["id"] == institution_id:
            return institution
    raise HTTPException(status_code=404, detail="Institution not found")


@router.get("/system/health")
async def system_health():
    """Get system health status"""
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "database": "operational",
            "agents": "operational",
            "memory": "operational"
        },
        "version": "1.0.0"
    }


@router.get("/system/stats")
async def system_stats():
    """Get system statistics"""
    return {
        "total_citizens": len(citizens_db),
        "total_tasks": len(tasks_db),
        "total_institutions": len(institutions_db),
        "active_agents": 8,
        "success_rate": 0.95
    }
