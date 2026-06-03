import aiohttp


class FetchError(Exception):
    def __init__(
        self,
        message: str,
        retryable: bool = True
    ):
        super().__init__(message)

        self.retryable = retryable

async def fetch_xml(
    url: str
) -> str:
    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            async with session.get(url) as response:
                if response.status == 404:
                    raise FetchError(
                        "Feed not found (404)",
                        retryable=False
                    )

                if response.status >= 400:
                    raise FetchError(
                        f"HTTP {response.status}",
                        retryable=True
                    )
                return await response.text()

    except aiohttp.ClientError as exc:
        raise FetchError(
            f"Network error while fetching URL: {str(exc)}"
        ) from exc