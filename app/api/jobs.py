from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import JobStatus, TaskStatus
from app.models.job import Job
from app.models.job_task import JobTask
from app.schemas.job import JobCreateRequest, JobCreateResponse
from app.workers.job_worker import process_job

from datetime import datetime

from fastapi import HTTPException

from app.schemas.job import (
    JobCreateRequest,
    JobCreateResponse,
    JobStatusResponse,
    JobTaskResponse
)

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)


@router.post(
    "",
    response_model=JobCreateResponse
)
def create_job(
    payload: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    job = Job(
        status=JobStatus.PENDING,
        total_urls=len(payload.urls)
    )

    db.add(job)
    db.flush()

    tasks = [
        JobTask(
            job_id=job.id,
            url=str(url),
            status=TaskStatus.PENDING
        )
        for url in payload.urls
    ]

    db.add_all(tasks)

    db.commit()

    background_tasks.add_task(
        process_job,
        job.id,
        db
    )

    return JobCreateResponse(
        job_id=job.id,
        status=job.status.value
    )

@router.get(
    "/{job_id}",
    response_model=JobStatusResponse
)
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    job = (
        db.query(Job)
        .filter(Job.id == job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    in_progress_urls = (
        db.query(JobTask)
        .filter(
            JobTask.job_id == job_id,
            JobTask.status == TaskStatus.IN_PROGRESS
        )
        .count()
    )

    pending_urls = (
        db.query(JobTask)
        .filter(
            JobTask.job_id == job_id,
            JobTask.status == TaskStatus.PENDING
        )
        .count()
    )

    elapsed_seconds = None

    if job.started_at:
        end_time = job.completed_at or datetime.utcnow()

        elapsed_seconds = (
            end_time - job.started_at
        ).total_seconds()

    return JobStatusResponse(
        job_id=job.id,
        status=job.status.value,

        total_urls=job.total_urls,
        completed_urls=job.completed_urls,
        failed_urls=job.failed_urls,
        in_progress_urls=in_progress_urls,
        pending_urls=pending_urls,

        elapsed_seconds=elapsed_seconds
    )

@router.get(
    "/{job_id}/tasks",
    response_model=list[JobTaskResponse]
)
def get_job_tasks(
    job_id: str,
    db: Session = Depends(get_db)
):
    tasks = (
        db.query(JobTask)
        .filter(JobTask.job_id == job_id)
        .all()
    )

    return [
        JobTaskResponse(
            url=task.url,
            status=task.status.value,

            attempts=task.attempts,
            records_extracted=task.records_extracted,

            error_message=task.error_message,

            started_at=task.started_at,
            completed_at=task.completed_at,
            failed_at=task.failed_at
        )
        for task in tasks
    ]