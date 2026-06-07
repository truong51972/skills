# Task Design

Use this reference when writing or reviewing Celery task functions, retry
policy, acknowledgement behavior, Beat jobs, and observability.

## Thin Task Wrapper

```python
from typing import Any

import httpx
from celery import Task, shared_task
from pydantic import BaseModel, ConfigDict

from my_worker.bootstrap import get_container


class ProcessOrderPayload(BaseModel):
    job_id: str
    order_id: str

    model_config = ConfigDict(extra="forbid")


@shared_task(
    bind=True,
    name="orders.process_order",
    autoretry_for=(httpx.TimeoutException, httpx.TransportError),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def process_order(self: Task, raw_payload: dict[str, Any]) -> dict[str, Any]:
    payload = ProcessOrderPayload.model_validate(raw_payload)
    service = get_container().order_service()

    result = service.process_order(
        job_id=payload.job_id,
        order_id=payload.order_id,
        task_id=self.request.id,
    )

    return {
        "job_id": payload.job_id,
        "status": result.status,
    }
```

Task wrappers should do only five things:

- Validate and normalize the message payload.
- Read task metadata such as `self.request.id`, retries, and delivery info.
- Delegate to a service method.
- Translate transient failures into bounded retry behavior.
- Return JSON-serializable results.

## Payload Rules

- Pass IDs, compact primitives, and small DTOs. Do not pass ORM models, files,
  large blobs, database sessions, or framework request objects.
- Include a stable `job_id`, `request_id`, or business idempotency key for every
  side-effecting task.
- Use Pydantic models for payload validation at the task boundary.
- Treat payload schema changes as public contract changes. Add optional fields
  or versioned tasks when producers and consumers deploy independently.

## Retry and Acknowledgement Policy

- Use `autoretry_for` only for transient infrastructure failures such as
  timeouts, connection resets, rate limits, and temporary upstream errors.
- Do not auto-retry validation errors, permission failures, missing domain data,
  or permanent business-rule failures.
- Use bounded retries with backoff and jitter.
- `acks_late=True` means the message is acknowledged after execution. Pair it
  with idempotency because duplicates can occur.
- `task_reject_on_worker_lost=True` can requeue tasks when a child process is
  killed, but it can also create message loops. Enable it only for tasks that
  can tolerate duplicate execution and repeated worker loss.
- For normal Python exceptions, use retry behavior. Acknowledgements protect
  against process or machine failures, not ordinary domain errors.

Prefer per-task policy:

```python
@shared_task(
    bind=True,
    name="reports.generate",
    autoretry_for=(TimeoutError, ConnectionError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def generate_report(self: Task, report_id: str, job_id: str) -> dict[str, str]:
    service = get_container().report_service()
    path = service.generate(report_id=report_id, job_id=job_id)
    return {"report_id": report_id, "path": path}
```

## Idempotency

An idempotent task can run more than once for the same logical job without
duplicating side effects.

Use one or more of these patterns:

- A durable job table keyed by `job_id`.
- Unique constraints around external side effects.
- Outbox/inbox records for message publication.
- Compare-and-set state transitions.
- Upserts instead of blind inserts.
- External API idempotency keys when the upstream supports them.

Do not claim a task is safe for late acknowledgement until duplicate execution
has been tested.

## Routing and Beat

- Keep default routing in `task_routes`.
- Use `.apply_async(queue=..., routing_key=...)` only for dynamic routing that
  truly depends on runtime data.
- Beat tasks should enqueue small commands. The task that does the work still
  needs idempotency because Beat can overlap during deploys or clock issues.
- Use locks or durable job records for scheduled jobs that must not overlap.

## Observability

Log with task and job context:

```python
logger.info(
    "order processing started",
    extra={
        "task_id": self.request.id,
        "job_id": payload.job_id,
        "order_id": payload.order_id,
        "retries": self.request.retries,
    },
)
```

Track queue latency, runtime, retries, failures by exception type, duplicate
dedupe hits, and worker shutdown behavior.
