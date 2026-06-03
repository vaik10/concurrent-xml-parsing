import asyncio
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.enums import JobStatus, TaskStatus
from app.models.job import Job
from app.models.job_task import JobTask

from app.services.fetcher import FetchError, fetch_xml
from app.services.parser import ParseError, parse_feed

from app.services.persistence import persist_records

from app.services.retry import fetch_with_retry

async def process_task(
    task: JobTask,
    job: Job,
    db: Session,
    semaphore: asyncio.Semaphore
):
    async with semaphore:
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow()

        db.commit()

        try:
            xml_content = await fetch_with_retry(
                fetch_coroutine=fetch_xml,
                url=task.url,
                task=task
            )
            records = parse_feed(xml_content)

            persist_records(
                db=db,
                job_task_id=task.id,
                records=records
            )

            task.records_extracted = len(records)

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()

            job.completed_urls += 1

        except (FetchError, ParseError) as exc:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            task.failed_at = datetime.utcnow()

            job.failed_urls += 1
        except Exception as exc:
            task.status = TaskStatus.FAILED
            task.error_message = f"Unexpected worker failure:: {str(exc)}"
            task.failed_at = datetime.utcnow()

            job.failed_urls += 1

        db.commit()

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

    semaphore = asyncio.Semaphore(2)

    await asyncio.gather(
        *[
            process_task(
                task=task,
                job=job,
                db=db,
                semaphore=semaphore
            )
            for task in tasks
        ]
    )

    if job.failed_urls == job.total_urls:
        job.status = JobStatus.FAILED
    else:
        job.status = JobStatus.COMPLETED

    job.completed_at = datetime.utcnow()

    db.commit()