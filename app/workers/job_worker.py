import asyncio
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.enums import JobStatus, TaskStatus
from app.models.job import Job
from app.models.job_task import JobTask


async def process_job(
    job_id: str,
    db: Session
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        return

    job.status = JobStatus.IN_PROGRESS
    job.started_at = datetime.utcnow()

    db.commit()

    tasks = (
        db.query(JobTask)
        .filter(JobTask.job_id == job_id)
        .all()
    )

    for task in tasks:
        task.status = TaskStatus.IN_PROGRESS

        db.commit()

        await asyncio.sleep(2)

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()

        job.completed_urls += 1

        db.commit()

    job.status = JobStatus.COMPLETED
    job.completed_at = datetime.utcnow()

    db.commit()