from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import JobStatus, TaskStatus
from app.models.job import Job
from app.models.job_task import JobTask
from app.schemas.job import JobCreateRequest, JobCreateResponse
from app.workers.job_worker import process_job

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