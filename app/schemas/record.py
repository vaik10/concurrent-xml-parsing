from typing import Optional

from pydantic import BaseModel


class FeedRecord(BaseModel):
    title: Optional[str] = None
    link: Optional[str] = None
    published: Optional[str] = None
    author: Optional[str] = None
    summary: Optional[str] = None