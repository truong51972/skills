# Celery Configuration

Use this reference when creating the Celery app, applying settings, defining
queues/routes, or choosing worker runtime defaults.

## App Factory

Prefer a small `create_celery_app()` function plus a module-level `app` for the
Celery CLI.

```python
from celery import Celery
from kombu import Queue
from pydantic import PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "my_worker"
    broker_url: str
    result_backend: str | None = None

    task_default_queue: str = "default"
    timezone: str = "UTC"
    worker_concurrency: PositiveInt | None = None
    worker_prefetch_multiplier: PositiveInt = 1

    task_soft_time_limit: PositiveInt | None = 840
    task_time_limit: PositiveInt | None = 900
    worker_soft_shutdown_timeout: float = 30.0
    broker_visibility_timeout: PositiveInt | None = None

    model_config = SettingsConfigDict(
        env_prefix="WORKER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def create_celery_app(settings: Settings | None = None) -> Celery:
    settings = settings or Settings()
    app = Celery(
        settings.app_name,
        include=[
            "my_worker.tasks.orders",
            "my_worker.tasks.reports",
        ],
    )

    transport_options: dict[str, int] = {}
    if settings.broker_visibility_timeout is not None:
        transport_options["visibility_timeout"] = settings.broker_visibility_timeout

    celery_config: dict[str, object] = dict(
        broker_url=settings.broker_url,
        result_backend=settings.result_backend,
        broker_connection_retry_on_startup=True,
        broker_transport_options=transport_options,
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        task_ignore_result=settings.result_backend is None,
        task_track_started=settings.result_backend is not None,
        enable_utc=True,
        timezone=settings.timezone,
        task_default_queue=settings.task_default_queue,
        task_default_routing_key=settings.task_default_queue,
        task_create_missing_queues=False,
        task_queues=(
            Queue(settings.task_default_queue, routing_key=settings.task_default_queue),
            Queue("io", routing_key="io"),
            Queue("cpu", routing_key="cpu"),
        ),
        task_routes={
            "orders.process_order": {
                "queue": "io",
                "routing_key": "io",
            },
            "reports.generate": {
                "queue": "cpu",
                "routing_key": "cpu",
            },
        },
        worker_prefetch_multiplier=settings.worker_prefetch_multiplier,
        task_soft_time_limit=settings.task_soft_time_limit,
        task_time_limit=settings.task_time_limit,
        worker_soft_shutdown_timeout=settings.worker_soft_shutdown_timeout,
    )

    if settings.worker_concurrency is not None:
        celery_config["worker_concurrency"] = settings.worker_concurrency

    app.conf.update(celery_config)
    return app


app = create_celery_app()
```

## Configuration Rules

- Use lowercase Celery settings. Avoid legacy uppercase names in new projects.
- Keep required settings explicit: a worker should fail fast if `broker_url` is
  missing.
- Keep result backends optional. Many fire-and-forget workloads do not need
  stored results.
- Set `task_ignore_result=True` when no result backend is configured.
- Use JSON serializers by default. Avoid pickle unless the security boundary is
  fully controlled.
- Prefer per-task acknowledgement and retry policy. Global `task_acks_late=True`
  is only safe when every task is idempotent.
- Use `worker_prefetch_multiplier=1` for long-running or uneven workloads. Raise
  it only for short tasks where throughput matters more than fairness.
- Use soft and hard task time limits together: the soft limit gives services a
  chance to clean up before the hard limit terminates execution.

## Broker Notes

**Redis**

- Redis is convenient for development and many production workloads, but it is
  not AMQP. Keep queue names, exchanges, and routing keys simple and aligned.
- For long tasks, set `broker_transport_options["visibility_timeout"]` longer
  than the maximum expected runtime plus deployment shutdown buffer.
- Be careful with ETA/countdown tasks longer than the visibility timeout because
  messages can be redelivered.

**RabbitMQ**

- RabbitMQ is the strongest default when advanced routing, exchanges, priorities,
  and operational visibility matter.
- Define queues with `kombu.Queue`; use `task_routes` rather than hard-coding
  routing in services.
- Consider quorum queues only when the operational tradeoffs are understood.

**SQS**

- Set `broker_transport_options["visibility_timeout"]` longer than the maximum
  processing window. A too-short timeout can produce duplicate execution.
- SQS does not support every Celery feature. Validate remote control, events,
  priority, and Beat assumptions in the target deployment.
- Long polling settings can reduce cost and idle CPU usage.

## Worker Commands

```bash
celery -A my_worker.main:app worker --loglevel=INFO -Q default,io --hostname=io@%h
celery -A my_worker.main:app worker --loglevel=INFO -Q cpu --concurrency=2 --hostname=cpu@%h
celery -A my_worker.main:app beat --loglevel=INFO
```

Run dedicated workers for queues with different runtime profiles. CPU-heavy,
IO-heavy, GPU, and callback workloads usually deserve separate queues and
different concurrency settings.
