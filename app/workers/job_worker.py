import asyncio
import structlog

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.enums import JobStatus, TaskStatus
from app.models.job import Job
from app.models.job_task import JobTask

from app.services.fetcher import FetchError, fetch_xml
from app.services.parser import ParseError, parse_feed

from app.services.persistence import persist_records

from app.services.retry import fetch_with_retry

from app.db.session import SessionLocal

logger = structlog.get_logger() 

async def process_task(
    task_id: int,
    job_id: str,
    semaphore: asyncio.Semaphore
):
    async with semaphore:
        db = SessionLocal()

        try:
            job = (
                db.query(Job)
                .filter(Job.id == job_id)
                .first()
            )

            task = (
                db.query(JobTask)
                .filter(JobTask.id == task_id)
                .first()
            )

            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.utcnow()

            db.commit()

            logger.info(
                "fetch_started",
                job_id=job.id,
                task_id=task.id,
                url=task.url
            )

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

                logger.info(
                    "task_completed",
                    job_id=job.id,
                    task_id=task.id,
                    url=task.url,
                    records_extracted=len(records)
                )

            except (FetchError, ParseError) as exc:
                task.status = TaskStatus.FAILED
                task.error_message = str(exc)
                task.failed_at = datetime.utcnow()

                job.failed_urls += 1

                logger.error(
                    "task_failed",
                    job_id=job.id,
                    task_id=task.id,
                    url=task.url,
                    error=str(exc)
                )

            except Exception as exc:
                task.status = TaskStatus.FAILED
                task.error_message = (
                    f"Unexpected worker failure: {str(exc)}"
                )
                task.failed_at = datetime.utcnow()

                job.failed_urls += 1

                logger.error(
                    "unexpected_task_failure",
                    job_id=job.id,
                    task_id=task.id,
                    url=task.url,
                    error=str(exc)
                )

            db.commit()

        finally:
            db.close()
async def process_job(
    job_id: str,
    db: Session
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        return

    job.status = JobStatus.IN_PROGRESS
    job.started_at = datetime.utcnow()

    logger.info(
        "job_started",
        job_id=job.id,
        total_urls=job.total_urls
    )

    db.commit()

    tasks = (
        db.query(JobTask)
        .filter(JobTask.job_id == job_id)
        .all()
    )

    semaphore = asyncio.Semaphore(10)

    await asyncio.gather(
        *[
            process_task(
                task_id=task.id,
                job_id=job.id,
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

    logger.info(
        "job_completed",
        job_id=job.id,
        completed_urls=job.completed_urls,
        failed_urls=job.failed_urls,
        final_status=job.status.value
    )

    db.commit()