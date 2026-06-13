# API Layer Reference

## Choose the smallest suitable DRF primitive

### Use APIView when

Use `APIView` for command-style or workflow endpoints with no standard CRUD shape:

- approve / reject / archive / restore / submit / publish
- import / export / commit / retry-job / start-processing

```python
class ResourceArchiveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, resource_id):
        resource = resource_get_visible(
            user=request.user,
            resource_id=resource_id,
        )
        archive_resource(resource=resource, actor=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
```

### Use GenericAPIView when

Use `GenericAPIView` when you want DRF hooks (`get_queryset`, `get_serializer_class`, `get_object`, pagination, filtering, schema) but the endpoint is not a simple generic CRUD view.

### Use generic views when

Use built-in generic views for simple resource operations:

```python
class ResourceListAPIView(ListAPIView):
    serializer_class = ResourceListOutputSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return resource_list(user=self.request.user)
```

Good choices: `ListAPIView`, `RetrieveAPIView`, `CreateAPIView`, `UpdateAPIView`, `DestroyAPIView`, `ListCreateAPIView`, `RetrieveUpdateDestroyAPIView`.

### Use ViewSet when

Use `ViewSet` when multiple actions belong naturally to one resource namespace and their permission and serializer logic is consistent enough to group.

**Prefer a separate `APIView` over a ViewSet `@action` when:**
- The action has its own distinct input or output serializer
- The action has different permission logic from the other actions
- The action is a complex workflow, not a simple state mutation
- Putting it in the ViewSet would require many special-case branches in `get_serializer_class` or `get_permissions`

```python
# Prefer this for complex commands:
class ResourceSubmitAPIView(APIView): ...

# Over this, when the action diverges heavily from the ViewSet:
class ResourceViewSet(ModelViewSet):
    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None): ...
```

### Use ModelViewSet when

Use `ModelViewSet` only when the resource is truly CRUD-like and business rules are simple.

Avoid `ModelViewSet` when:
- Create or update has complex workflows
- Permissions vary heavily per action
- Actions are mostly commands
- Each action needs different input/output serializers
- Side effects or jobs are involved
- Object access is complex

## Views should be thin

A view may:
- Check authentication / permission
- Parse and validate input
- Fetch scoped object or queryset
- Call service or selector
- Serialize output
- Return HTTP status

A view should not:
- Contain large business workflows
- Build complex database queries inline
- Perform unscoped object lookups
- Mutate many models directly without a service

## Prefer request-aware get_queryset

```python
def get_queryset(self):
    return Resource.objects.visible_to(self.request.user)
```

Avoid relying on a static `queryset` class attribute for APIs that need ownership, tenant scoping, or request-specific filtering.

## Object access pattern

Always scope before lookup:

```python
# Correct
resource = get_object_or_404(
    Resource.objects.visible_to(request.user),
    id=resource_id,
)

# Wrong — bypasses ownership check
resource = get_object_or_404(Resource, id=resource_id)
```

For multi-tenant APIs, chain both scopes:

```python
resource = get_object_or_404(
    Resource.objects.for_tenant(tenant).visible_to(user),
    id=resource_id,
)
```

## Input/output serializer pattern

```python
input_serializer = ResourceCreateInputSerializer(data=request.data)
input_serializer.is_valid(raise_exception=True)

resource = resource_create(
    actor=request.user,
    **input_serializer.validated_data,
)

output_serializer = ResourceDetailOutputSerializer(resource)
return Response(output_serializer.data, status=status.HTTP_201_CREATED)
```

## Filtering

Keep filtering explicit and validated.

**With a filter serializer (lightweight, no extra dependency):**

```python
class ResourceFilterSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Resource.Status.choices, required=False)
    search = serializers.CharField(required=False, allow_blank=True)
```

Pass validated filters to selector:

```python
filter_serializer = ResourceFilterSerializer(data=request.query_params)
filter_serializer.is_valid(raise_exception=True)
queryset = resource_list(user=request.user, filters=filter_serializer.validated_data)
```

**With django-filter:** If the project already uses `django-filter`, prefer `DjangoFilterBackend` for simple field equality filters. For complex cross-field or permission-aware filters, prefer the explicit filter serializer approach so the logic stays testable and visible.

Avoid parsing raw `request.query_params` inline throughout views.

## Response status guide

| Status | When to use |
|---|---|
| `200 OK` | Successful read or update with body |
| `201 Created` | Resource created |
| `202 Accepted` | Async job accepted |
| `204 No Content` | Successful mutation, no body |
| `400 Bad Request` | Validation or malformed input |
| `401 Unauthorized` | Missing or invalid authentication |
| `403 Forbidden` | Authenticated but not allowed |
| `404 Not Found` | Not visible or does not exist |
| `409 Conflict` | State conflict or concurrency conflict |
| `422 Unprocessable Entity` | Semantic validation (only if project uses it consistently) |

> For private resources, prefer returning `404` for non-visible objects rather than `403`, to avoid leaking existence.

## Pagination

List endpoints should be paginated by default unless the result set is guaranteed small and bounded. Never serialize large unbounded querysets.

## URL design

```text
# Resource CRUD
/api/v1/resources/
/api/v1/resources/{resource_id}/

# Commands
/api/v1/resources/{resource_id}/archive/
/api/v1/resources/{resource_id}/restore/
/api/v1/resources/{resource_id}/submit/

# Parent-scoped lists
/api/v1/projects/{project_id}/resources/
```

Avoid nesting beyond 2–3 levels unless there is a strong domain reason.

## Versioning

Use clear API version namespaces:

```text
/api/v1/...
/api/v2/...
```

Keep versioned serializers, views, and URLs together. Do not silently change request or response shapes within the same public API version.
