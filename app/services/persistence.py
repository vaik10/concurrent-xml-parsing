from sqlalchemy.orm import Session

from app.models.feed_record import FeedRecord
from app.schemas.record import FeedRecord as FeedRecordSchema


def persist_records(
    db: Session,
    job_task_id: int,
    records: list[FeedRecordSchema]
):
    db_records = [
        FeedRecord(
            job_task_id=job_task_id,
            title=record.title,
            link=record.link,
            published=record.published,
            author=record.author,
            summary=record.summary
        )
        for record in records
    ]

    db.add_all(db_records)

    db.commit()