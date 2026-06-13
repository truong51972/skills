# Async Jobs Reference

## When to return 202 Accepted

Return `202 Accepted` when the API accepts work that will complete asynchronously:

- Document processing, imports, exports, report generation
- Batch updates, indexing, ML/AI pipeline execution
- Long-running external calls
- Webhook retry, background reconciliation

## Endpoint responsibility

The DRF endpoint should:
- Authenticate and authorize the caller
- Validate input
- Fetch scoped objects
- Call a service that creates the job record and enqueues the task
- Return job/resource status immediately

The endpoint should never run the long task inline.

## Response shape for 202

Return a stable, predictable shape:

```json
{
  "job_id": "job_123",
  "status": "queued",
  "resource_id": "res_123",
  "status_url": "/api/v1/jobs/job_123/"
}
```

Include `status_url` when clients will need to poll for completion.

## View pattern

```python
class ResourceProcessAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, resource_id):
        resource = resource_get_visible(
            user=request.user,
            resource_id=resource_id,
        )

        input_serializer = ResourceProcessInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        job = resource_start_processing(
            resource=resource,
            actor=request.user,
            options=input_serializer.validated_data,
        )

        output_serializer = JobAcceptedOutputSerializer(job)
        return Response(output_serializer.data, status=status.HTTP_202_ACCEPTED)
```

## Service pattern

Create the job record and enqueue via `on_commit` to avoid enqueuing if the transaction rolls back:

```python
@transaction.atomic
def resource_start_processing(*, resource, actor, options):
    job = Job.objects.create(
        type=Job.Type.RESOURCE_PROCESSING,
        status=Job.Status.QUEUED,
        created_by=actor,
        resource_id=resource.id,
        payload=options,
    )

    transaction.on_commit(
        lambda: enqueue_resource_processing_job(job_id=job.id)
    )

    return job
```

## Job polling endpoint

Provide a status endpoint when clients need to observe completion:

```python
class JobDetailAPIView(RetrieveAPIView):
    serializer_class = JobDetailOutputSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Scope job visibility the same way you scope the resource
        return Job.objects.visible_to(self.request.user)
```

Apply the same ownership scoping to job objects as to the underlying resource. A user should not be able to poll another user's job by guessing the ID.

## Separate job status from resource status

Use two distinct status enums unless the domain is intentionally simple.

**Resource status** — describes the business object:
```python
class Status(models.TextChoices):
    DRAFT = "draft"
    ACTIVE = "active"
    PROCESSING = "processing"
    FAILED = "failed"
    ARCHIVED = "archived"
```

**Job status** — describes the background execution:
```python
class Status(models.TextChoices):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

## State transition guards

Do not allow invalid transitions. Always check preconditions in the service, not in the view:

```python
# Wrong: raw status assignment from input
resource.status = request.data["status"]
resource.save()

# Correct: named service function with guard
resource_submit_for_review(resource=resource, actor=request.user)

# Inside the service:
def resource_submit_for_review(*, resource, actor):
    if resource.status != Resource.Status.DRAFT:
        raise ResourceStateError("Only draft resources can be submitted.")
    ...
```

## Idempotency

For endpoints that may be retried (mobile clients, webhook receivers, payment-like operations, imports), consider idempotency.

Possible approaches:
- Client-provided idempotency key stored on the job record
- Unique constraint on (resource_id, job_type) when only one active job is allowed
- Deduplication by payload hash
- Reject duplicate active jobs with `409 Conflict` and return the existing job

## Error handling contract

Before shipping an async endpoint, define clearly:

| Question | Answer to document |
|---|---|
| What happens if enqueue fails? | Roll back the transaction so no orphaned job record is created |
| Is the job row created before enqueue? | Yes — always. The job record is the source of truth |
| If enqueue fails, does the transaction roll back? | Yes, via `on_commit` pattern |
| How does the client observe failure? | Poll `status_url`; failed jobs set `status = failed` and optionally `error_detail` |
| Is the operation idempotent? | Specify yes/no and the deduplication strategy |
| What is the retry behavior? | Specify max retries and backoff in the worker, not the API |

## External side effects

Do not call slow external systems inside DB transactions.

Preferred flow:
1. Write DB state and create job record
2. Commit transaction
3. Enqueue task via `on_commit`
4. Worker performs the slow work
5. Worker updates job and resource status when done
