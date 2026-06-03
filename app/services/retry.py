import asyncio

from app.services.fetcher import FetchError


MAX_RETRIES = 3


async def fetch_with_retry(
    fetch_coroutine,
    url: str
):
    for attempt in range(MAX_RETRIES):
        try:
            return await fetch_coroutine(url)

        except FetchError as exc:
            if not exc.retryable:
                raise exc

            if attempt == MAX_RETRIES - 1:
                raise exc

            backoff_seconds = 2 ** attempt

            await asyncio.sleep(backoff_seconds)