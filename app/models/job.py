from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import JobStatus


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4())
    )

    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus),
        default=JobStatus.PENDING,
        nullable=False
    )

    total_urls: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    completed_urls: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    failed_urls: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )

    completed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )

    tasks = relationship(
        "JobTask",
        back_populates="job",
        cascade="all, delete-orphan"
    )