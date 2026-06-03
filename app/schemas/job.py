from typing import List

from pydantic import BaseModel, HttpUrl, Field

from datetime import datetime
from typing import Optional

class JobCreateRequest(BaseModel):
    urls: List[HttpUrl] = Field(
        ...,
        min_length=1,
        max_length=120
    )

class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str

    total_urls: int
    completed_urls: int
    failed_urls: int
    in_progress_urls: int
    pending_urls: int

    elapsed_seconds: Optional[float] = None

class JobTaskResponse(BaseModel):
    url: str
    status: str

    attempts: int
    records_extracted: int

    error_message: Optional[str] = None

    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None