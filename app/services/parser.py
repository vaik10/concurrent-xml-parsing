import feedparser

from app.schemas.record import FeedRecord


class ParseError(Exception):
    pass


def parse_feed(
    xml_content: str
) -> list[FeedRecord]:

    parsed_feed = feedparser.parse(xml_content)

    if parsed_feed.bozo:
        raise ParseError(
            "Malformed or invalid XML feed"
        )

    records = []

    for entry in parsed_feed.entries:
        record = FeedRecord(
            title=entry.get("title"),
            link=entry.get("link"),
            published=entry.get("published"),
            author=entry.get("author"),
            summary=entry.get("summary")
        )

        records.append(record)

    return records