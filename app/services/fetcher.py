import aiohttp


class FetchError(Exception):
    pass


async def fetch_xml(
    url: str
) -> str:
    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            async with session.get(url) as response:
                if response.status != 200:
                    raise FetchError(
                        f"Failed to fetch URL: HTTP {response.status}"
                    )

                return await response.text()

    except aiohttp.ClientError as exc:
        raise FetchError(
            f"Network error while fetching URL: {str(exc)}"
        ) from exc