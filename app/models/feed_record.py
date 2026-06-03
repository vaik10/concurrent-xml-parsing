from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FeedRecord(Base):
    __tablename__ = "feed_records"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    job_task_id: Mapped[int] = mapped_column(
        ForeignKey("job_tasks.id")
    )

    title: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    link: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    published: Mapped[str] = mapped_column(
        String,
        nullable=True
    )

    author: Mapped[str] = mapped_column(
        String,
        nullable=True
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    task = relationship(
        "JobTask",
        back_populates="records"
    )