from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, Boolean, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database

DATABASE_URL = "sqlite:///./test.db"

database = Database(DATABASE_URL)
metadata = MetaData()

Base = declarative_base(metadata=metadata)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    completed = Column(Boolean, default=False)

engine = create_engine(DATABASE_URL)  # for FastAPI
metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()

class TaskCreate(BaseModel):
    title: str
    description: str

class TaskUpdate(BaseModel):
    title: str
    description: str
    completed: bool

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/tasks/", response_model=TaskResponse)
async def create_task(task: TaskCreate):
    query = Task.__table__.insert().values(title=task.title, description=task.description, completed=False)
    last_record_id = await database.execute(query)
    return {**task.dict(), "id": last_record_id, "completed": False}

@app.get("/tasks/", response_model=List[TaskResponse])
async def read_tasks(skip: int = 0, limit: int = 10):
    query = Task.__table__.select().offset(skip).limit(limit)
    return await database.fetch_all(query)

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def read_task(task_id: int):
    query = Task.__table__.select().where(Task.id == task_id)
    task = await database.fetch_one(query)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task: TaskUpdate):
    query = Task.__table__.update().where(Task.id == task_id).values(title=task.title, description=task.description, completed=task.completed)
    await database.execute(query)
    return {**task.dict(), "id": task_id}


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    query = Task.__table__.delete().where(Task.id == task_id)
    await database.execute(query)
    return {"detail": "Task deleted"}
