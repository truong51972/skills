# Async Jobs Reference

## When to return 202 Accepted

Return `202 Accepted` when the API accepts work that will complete later.

Examples:

- document processing
- imports
- exports
- report generation
- batch updates
- indexing
- long-running external calls
- ML/AI pipeline execution
- webhook retry
- background reconciliation

## Endpoint responsibility

The DRF endpoint should:

- authenticate and authorize the caller
- validate input
- fetch scoped objects
- call a service
- create or enqueue a job through the service
- return job/resource status

The endpoint should not run the long task inline.

## Response shape

Use a stable response shape:

```json
{
  "job_id": "job_123",
  "status": "queued",
  "resource_id": "res_123"
}
````

Optionally include a polling URL:

```json
{
  "job_id": "job_123",
  "status": "queued",
  "resource_id": "res_123",
  "status_url": "/api/v1/jobs/job_123/"
}
```

## Service pattern

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

## Idempotency

For endpoints that may be retried, consider idempotency.

Useful cases:

* payment-like operations
* imports
* webhooks
* batch jobs
* expensive processing
* mobile clients with unstable networks

Possible approaches:

* client-provided idempotency key
* unique job per resource/state
* deduplicate by payload hash
* reject duplicate active jobs with `409 Conflict`
* return existing job if one is already queued/running

## State transitions

Do not allow invalid transitions.

Bad:

```python
resource.status = request.data["status"]
resource.save()
```

Good:

```python
resource_submit_for_review(resource=resource, actor=request.user)
```

Inside service:

```python
if resource.status != Resource.Status.DRAFT:
    raise ResourceStateError("Only draft resources can be submitted.")
```

## Job and resource status

Separate job status from resource status when possible.

Resource status describes the business object:

* draft
* active
* archived
* processing
* failed

Job status describes the background execution:

* queued
* running
* succeeded
* failed
* cancelled

Avoid mixing them unless the domain is intentionally simple.

## Error handling

Async endpoints should define:

* what happens if enqueue fails
* whether job row is created before enqueue
* whether failed enqueue rolls back the transaction
* how the frontend/client observes failure
* retry behavior
* whether the operation is idempotent

## External side effects

Do not call slow external systems inside DB transactions.

Prefer:

1. write DB state
2. commit transaction
3. enqueue job or side effect
4. let worker perform slow work
5. worker updates job/resource state