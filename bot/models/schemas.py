from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_serializer


class Category(BaseModel):
    """Модель категории"""

    id: str
    name: str
    created_at: datetime


class Task(BaseModel):
    """Модель задачи"""

    id: str
    title: str
    description: Optional[str] = None
    created_at: datetime
    due_date: Optional[datetime] = None
    is_completed: bool
    categories: List[Category] = []
    telegram_user_id: int


class CreateTaskRequest(BaseModel):
    """Запрос на создание задачи"""

    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    category_ids: Optional[List[str]] = None


class UpdateTaskRequest(BaseModel):
    """Запрос на обновление задачи"""

    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    category_ids: Optional[List[str]] = None
    is_completed: Optional[bool] = None

    class Config:
        extra = "forbid"


class CreateCategoryRequest(BaseModel):
    """Запрос на создание категории"""

    name: str
