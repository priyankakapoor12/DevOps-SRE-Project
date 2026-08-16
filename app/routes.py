from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas
from .database import get_db

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    """Create a new task"""
    db_task = models.Task(
        title=task.title,
        description=task.description,
        priority=task.priority
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("/", response_model=List[schemas.TaskResponse])
async def get_tasks(
    skip: int = 0,
    limit: int = 100,
    completed: bool = None,
    priority: str = None,
    db: Session = Depends(get_db)
):
    """Get all tasks with optional filters"""
    query = db.query(models.Task)

    if completed is not None:
        query = query.filter(models.Task.completed == completed)

    if priority:
        query = query.filter(models.Task.priority == priority)

    tasks = query.offset(skip).limit(limit).all()
    return tasks


@router.get("/{task_id}", response_model=schemas.TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task by ID"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    return task


@router.put("/{task_id}", response_model=schemas.TaskResponse)
async def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: Session = Depends(get_db)
):
    """Update a task"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )

    # Update only provided fields
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )

    db.delete(task)
    db.commit()
    return None


@router.get("/stats/summary")
async def get_task_statistics(db: Session = Depends(get_db)):
    """Get task statistics"""
    total = db.query(models.Task).count()
    completed = db.query(models.Task).filter(models.Task.completed == True).count()
    pending = total - completed

    # Count by priority
    high_priority = db.query(models.Task).filter(models.Task.priority == "high").count()
    medium_priority = db.query(models.Task).filter(models.Task.priority == "medium").count()
    low_priority = db.query(models.Task).filter(models.Task.priority == "low").count()

    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "by_priority": {
            "high": high_priority,
            "medium": medium_priority,
            "low": low_priority
        }
    }
