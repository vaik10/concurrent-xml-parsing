from typing import List

from pydantic import BaseModel, HttpUrl


class JobCreateRequest(BaseModel):
    urls: List[HttpUrl]


class JobCreateResponse(BaseModel):
    job_id: str
    status: str