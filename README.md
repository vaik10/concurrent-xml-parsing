# Concurrent XML Processing Pipeline

An asynchronous XML ingestion pipeline built with FastAPI, PostgreSQL, and asyncio. The system concurrently fetches, parses, and persists RSS/XML feeds while exposing job-level and task-level monitoring APIs with structured logging and retry support.

---

# Architecture Overview

```text
                ┌──────────────┐
                │   Client     │
                └──────┬───────┘
                       │
                       ▼
              ┌────────────────┐
              │ FastAPI Server │
              └──────┬─────────┘
                     │
                     ▼
        ┌──────────────────────────┐
        │ Background Job Pipeline  │
        └──────────┬───────────────┘
                   │
         Concurrent Async Workers
                   │
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
 Fetch XML     Parse Feed     Persist Data
     │                             │
     └─────────────┬──────────────┘
                   ▼
             PostgreSQL
```

---

# Features

* Asynchronous XML feed processing
* Concurrent URL fetching using asyncio
* Configurable concurrency control using semaphores
* Structured JSON logging
* Retry strategy with exponential backoff
* RSS/XML parsing using feedparser
* Job-level and task-level monitoring APIs
* PostgreSQL persistence layer
* Dockerized local development environment
* Swagger/OpenAPI documentation

---

# Tech Stack

* FastAPI — asynchronous API framework
* PostgreSQL — relational persistence layer
* SQLAlchemy — ORM and session management
* asyncio + aiohttp — concurrent network processing
* feedparser — RSS/XML parsing
* structlog — structured JSON logging
* Docker Compose — local orchestration

---

# Project Structure

```text
app/
├── api/
├── core/
├── db/
├── models/
├── schemas/
├── services/
├── workers/
└── main.py
```

---

# Running Locally

## Prerequisites

* Docker
* Docker Compose

---

## Start Services

```bash
docker compose up --build
```

---

## API Documentation

Swagger UI:

```text
http://localhost:8000/docs
```

---

# API Endpoints

## Create Job

### Request

```bash
curl -X POST http://localhost:8000/jobs \
-H "Content-Type: application/json" \
-d '{
  "urls": [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"
  ]
}'
```

### Response

```json
{
  "job_id": "2bbfe3f5-2d4e-4df9-bce7-74a1bb74d2f",
  "status": "PENDING",
  "message": "Job created successfully"
}
```

---

## Get Job Status

### Request

```bash
curl http://localhost:8000/jobs/{job_id}
```

### Response

```json
{
  "job_id": "2bbfe3f5-2d4e-4df9-bce7-74a1bb74d2f",
  "status": "COMPLETED",
  "total_urls": 10,
  "completed_urls": 9,
  "failed_urls": 1,
  "in_progress_urls": 0,
  "pending_urls": 0,
  "elapsed_seconds": 5.72
}
```

---

## Get Job Tasks

### Request

```bash
curl http://localhost:8000/jobs/{job_id}/tasks
```

### Response

```json
[
  {
    "url": "https://feeds.bbci.co.uk/news/rss.xml",
    "status": "COMPLETED",
    "attempts": 1,
    "records_extracted": 32,
    "error_message": null,
    "started_at": "2026-06-03T18:00:00",
    "completed_at": "2026-06-03T18:00:02",
    "failed_at": null
  }
]
```

---

# Design Decisions

## Concurrency Model

The workload is primarily IO-bound due to network requests to external XML feeds. asyncio + aiohttp was chosen over threads or multiprocessing because asynchronous IO provides high concurrency with significantly lower overhead for network-bound workloads.

Concurrency is controlled using an asyncio semaphore to:

* avoid overwhelming external feed providers
* prevent excessive open socket usage
* reduce database contention

A concurrency limit of 10 workers was selected as a reasonable balance between throughput and resource usage for the assignment scale.

---

## Background Processing Strategy

The API immediately returns a `job_id` after persisting the job and task metadata. Actual processing occurs asynchronously in background worker tasks.

This approach:

* prevents long-running request blocking
* improves responsiveness
* better reflects production asynchronous processing systems

---

## Retry Strategy

Transient network failures are retried using exponential backoff with a maximum of 3 attempts.

Retryable failures:

* connection errors
* DNS resolution failures
* temporary HTTP failures

Non-retryable failures:

* malformed XML
* invalid feed formats
* HTTP 404 responses

This avoids unnecessary retries for permanent failures while improving resilience against temporary network issues.

---

## XML Parsing Strategy

`feedparser` was selected because:

* it handles both RSS and Atom feeds
* it gracefully tolerates imperfect feed formatting
* it significantly reduces XML parsing boilerplate

The parser uses the built-in `bozo` detection flag to identify malformed feeds.

---

## Logging Strategy

Structured JSON logging was implemented using `structlog`.

All logs include contextual metadata such as:

* job_id
* task_id
* URL
* execution status
* records extracted

This enables efficient debugging and traceability for asynchronous concurrent workloads.

Example log:

```json
{
  "event": "task_completed",
  "job_id": "123",
  "task_id": 5,
  "url": "https://feeds.bbci.co.uk/news/rss.xml",
  "records_extracted": 32,
  "timestamp": "2026-06-03T18:00:00Z",
  "level": "info"
}
```

---

## Database Session Isolation

Each concurrent worker task creates its own SQLAlchemy session to avoid shared mutable session state across async execution contexts.

This prevents:

* stale ORM state
* race conditions
* transaction inconsistencies
* session synchronization issues

---

# Tradeoffs

## Why no Celery/RabbitMQ?

For the assignment scale (100 URLs), asyncio-based concurrency provided sufficient throughput while keeping the architecture simpler and easier to operate locally.

Introducing Celery and a message broker would add operational complexity without significant benefits at this scale.

---

## Why synchronous SQLAlchemy sessions?

Database operations are lightweight relative to network IO, so synchronous SQLAlchemy sessions were chosen to reduce complexity while maintaining acceptable performance.

The primary bottleneck in this workload is external network latency rather than database throughput.

---

## Why not store raw XML payloads?

The current implementation persists only normalized feed records. Persisting raw XML payloads could improve auditability and replayability but would increase storage requirements and implementation complexity.

---

# Scaling Considerations

## 10x Scale (1000 URLs)

Potential bottlenecks:

* increased DB write contention
* growing memory usage from concurrent tasks
* excessive HTTP connections
* slower aggregate status queries

Potential improvements:

* bulk database inserts
* connection pooling optimization
* worker batching
* pagination for task APIs
* more granular concurrency controls

---

## 100x Scale (10,000 URLs)

At larger scales the current single-process architecture would become insufficient.

Likely architectural changes:

* distributed task queues (Celery/RabbitMQ/Kafka)
* horizontally scaled worker nodes
* dedicated ingestion and persistence services
* rate limiting and adaptive backpressure
* partitioned databases or read replicas
* centralized log aggregation
* object storage for raw XML archival

The primary bottlenecks at this scale would likely be:

* database write throughput
* network socket exhaustion
* retry storms during provider outages
* monitoring query costs
* memory pressure from high task concurrency

---

# Failure Handling

The system distinguishes between retryable and non-retryable failures.

## Retryable Failures

* DNS resolution failures
* temporary connection failures
* transient HTTP failures

## Non-Retryable Failures

* malformed XML
* invalid RSS/Atom feeds
* HTTP 404 responses

Task-level failures are persisted with:

* error message
* retry count
* timestamps
* execution status

---

# Observability

The system exposes:

* aggregate job-level execution status
* per-task execution visibility
* structured logs for all pipeline events

This enables:

* operational debugging
* execution tracing
* failure analysis
* throughput monitoring

---

# Future Improvements

* Alembic database migrations
* Distributed task queues
* Metrics export via Prometheus
* OpenTelemetry tracing
* Dead-letter queue handling
* Feed deduplication
* Batch persistence optimization
* Rate limiting per provider
* Configurable concurrency settings
* Persistent raw XML archival

---

# Local Development Notes

## Reset Database

```bash
docker compose down -v
```

---

## Rebuild Services

```bash
docker compose up --build
```

---

## View Logs

```bash
docker compose logs -f
```

---

# Demo Notes

The system was tested against the provided XML feed list and successfully:

* fetched feeds concurrently
* parsed RSS/XML content
* persisted structured feed records
* tracked execution status
* handled malformed and unreachable feeds gracefully
* exposed monitoring APIs for operational visibility
