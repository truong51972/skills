# Testing, Schema & Security Reference

## Test layers

### Service tests

Test business rules in isolation:
- Create / update / archive / restore behavior
- State transition guards (valid and invalid)
- Transaction behavior
- Side effects scheduled via `on_commit`
- Job creation and status changes

### Selector / QuerySet tests

Test read visibility:
- User can see their own resources
- User cannot see another user's resources
- Tenant scoping works correctly
- Archived / deleted rows are included or excluded per intent
- Filters return the expected subset

### API tests

Test the HTTP contract end-to-end:
- Auth required (unauthenticated → 401)
- Permission enforced (authenticated but not allowed → 403 or 404)
- Request validation (invalid input → 400 with field errors)
- Success status code and response shape
- Error shape on failure
- Cross-user access (user B cannot reach user A's objects)
- Pagination (list does not exceed page size)

## Required authorization tests

Every detail / update / delete / command endpoint should have:

```python
class ResourceDetailAPITests(APITestCase):

    def test_unauthenticated_request_is_rejected(self):
        resource = ResourceFactory()
        response = self.client.get(f"/api/v1/resources/{resource.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_can_access_own_resource(self):
        user = UserFactory()
        resource = ResourceFactory(owner=user)
        self.client.force_authenticate(user=user)
        response = self.client.get(f"/api/v1/resources/{resource.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_access_resource(self):
        user_a = UserFactory()
        user_b = UserFactory()
        resource = ResourceFactory(owner=user_a)
        self.client.force_authenticate(user=user_b)
        response = self.client.get(f"/api/v1/resources/{resource.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_does_not_expose_other_users_resources(self):
        user_a = UserFactory()
        user_b = UserFactory()
        ResourceFactory(owner=user_a)
        self.client.force_authenticate(user=user_b)
        response = self.client.get("/api/v1/resources/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
```

## Query count tests

Use query count tests for list endpoints where each row accesses a foreign key or related set — the most common N+1 source.

```python
def test_list_endpoint_query_count(self):
    user = UserFactory()
    ResourceFactory.create_batch(10, owner=user)
    self.client.force_authenticate(user=user)

    with self.assertNumQueries(3):  # e.g. auth + list + prefetch
        response = self.client.get("/api/v1/resources/")

    self.assertEqual(response.status_code, status.HTTP_200_OK)
```

> Do not overfit to exact query counts for volatile endpoints. Use this test when N+1 risk is meaningful — typically list endpoints where the serializer accesses related objects.

## Schema

For non-trivial endpoints, explicitly annotate schema with `drf-spectacular`:

```python
@extend_schema(
    request=ResourceCreateInputSerializer,
    responses={201: ResourceDetailOutputSerializer},
)
class ResourceCreateAPIView(APIView):
    ...

@extend_schema(
    request=ResourcePublishInputSerializer,
    responses={
        202: JobAcceptedOutputSerializer,
        409: OpenApiResponse(description="Resource is not in a publishable state"),
    },
)
class ResourcePublishAPIView(APIView):
    ...
```

For `SerializerMethodField` with non-obvious types, annotate the field:

```python
from drf_spectacular.utils import extend_schema_field

class ResourceOutputSerializer(serializers.ModelSerializer):
    tag_names = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_tag_names(self, obj):
        return [tag.name for tag in obj.tags.all()]
```

Without `@extend_schema_field`, drf-spectacular infers `SerializerMethodField` as `any` type, producing an inaccurate schema.

## Schema rules

Schema should document:
- Request body (with required/optional distinction)
- Response body per status code
- Query parameters for list endpoints
- Path parameters
- Auth requirements
- Error responses when they have meaningful structure

Do not rely solely on automatic schema generation for command-style or async endpoints — they have multiple response codes that need explicit mapping.

## Security: object-level authorization

Broken object-level authorization is the most common API security risk in DRF applications.

Every endpoint that accepts an object ID must verify:
- The object is visible to the calling user
- Parent-child relationships are validated (e.g. a comment must belong to the project the user can access)
- Tenant / project / org ownership is checked when applicable
- List and detail visibility are consistent

```python
# Wrong — trusts the ID without checking ownership
resource = Resource.objects.get(id=resource_id)

# Correct
resource = get_object_or_404(
    Resource.objects.visible_to(request.user),
    id=resource_id,
)
```

## Security: mass assignment

Do not expose sensitive fields for client writes. Use explicit input serializers:

Fields to always protect:
- `owner`, `tenant`, `organization`, `project`
- `role`, `is_staff`, `is_superuser`
- `status`, `approved_by`, `created_by`, `updated_by`
- Internal metadata, permission flags

## Security: default permissions

Use safe project-wide defaults. The risk is accidentally public endpoints, not accidentally protected ones.

For public endpoints, mark the decision clearly with a comment and add an explicit test:

```python
class ResourcePublicListAPIView(ListAPIView):
    permission_classes = []  # intentionally public — read-only product catalog
    ...
```

## Throttling

Consider throttling for:
- Login / session endpoints
- Expensive search
- Async job creation
- File upload, export, import
- AI / ML calls
- Public or unauthenticated APIs
- Webhook receivers

## Production review checklist

Before merging a DRF endpoint:

- [ ] Does it require authentication by default?
- [ ] Are permissions explicit and correct?
- [ ] Are all object lookups scoped to the caller?
- [ ] Does list visibility match detail visibility?
- [ ] Are input and output serializers explicit?
- [ ] Are server-owned fields protected from client writes?
- [ ] Is business logic outside the view and serializer?
- [ ] Are database invariants enforced with constraints where needed?
- [ ] Are common filter fields indexed?
- [ ] Are list endpoints paginated?
- [ ] Are relations optimized to avoid N+1?
- [ ] Are async operations returning 202?
- [ ] Are side effects outside the transaction (via `on_commit`)?
- [ ] Are there API tests covering user A vs user B access?
- [ ] Is the schema accurate for frontend/client usage?
- [ ] Are `SerializerMethodField` fields annotated with `@extend_schema_field`?
