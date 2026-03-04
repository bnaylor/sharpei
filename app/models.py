from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Table
from sqlalchemy.orm import relationship
from .database import Base

task_dependencies = Table(
    "task_dependencies",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),
    Column("depends_on_id", Integer, ForeignKey("tasks.id"), primary_key=True)
)

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    query = Column(String, nullable=True) # Search query for smart categories
    
    tasks = relationship("Task", back_populates="category")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    priority = Column(Integer, default=1) # 0 (High), 1 (Normal), 2 (Low)
    position = Column(Integer, default=0)
    hashtags = Column(String, nullable=True) # Stored as space-separated or comma-separated string
    recurrence = Column(String, nullable=True) # e.g., 'daily', 'weekly', 'monthly', or '7d', '14d'
    completed = Column(Boolean, default=False)
    archived = Column(Boolean, default=False)

    # Dependencies
    blocked_by = relationship(
        "Task",
        secondary=task_dependencies,
        primaryjoin=id == task_dependencies.c.task_id,
        secondaryjoin=id == task_dependencies.c.depends_on_id,
        back_populates="blocking"
    )
    blocking = relationship(
        "Task",
        secondary=task_dependencies,
        primaryjoin=id == task_dependencies.c.depends_on_id,
        secondaryjoin=id == task_dependencies.c.task_id,
        back_populates="blocked_by"
    )

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category", back_populates="tasks")

    parent_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    subtasks = relationship("Task", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("Task", back_populates="subtasks", remote_side=[id])

    @property
    def blocked_by_ids(self):
        return [t.id for t in self.blocked_by]

    @property
    def blocking_ids(self):
        return [t.id for t in self.blocking]
