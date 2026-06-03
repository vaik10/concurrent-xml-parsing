import asyncio

from app.services.fetcher import FetchError

from app.models.job_task import JobTask


MAX_RETRIES = 3


async def fetch_with_retry(
    fetch_coroutine,
    url: str,
    task: JobTask
):
    for attempt in range(MAX_RETRIES):
        try:
            task.attempts += 1

            return await fetch_coroutine(url)

        except FetchError as exc:
            if not exc.retryable:
                raise exc

            if attempt == MAX_RETRIES - 1:
                raise exc

            backoff_seconds = 2 ** attempt

            await asyncio.sleep(backoff_seconds)