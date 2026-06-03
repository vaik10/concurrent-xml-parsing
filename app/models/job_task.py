from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TaskStatus


class JobTask(Base):
    __tablename__ = "job_tasks"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    job_id: Mapped[str] = mapped_column(
        ForeignKey("jobs.id")
    )

    url: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False
    )

    records_extracted: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    error_message: Mapped[str] = mapped_column(
        String,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    completed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )

    job = relationship(
        "Job",
        back_populates="tasks"
    )

    records = relationship(
        "FeedRecord",
        back_populates="task",
        cascade="all, delete-orphan"
    )