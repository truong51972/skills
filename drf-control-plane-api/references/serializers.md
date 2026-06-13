# Serializers Reference

## Serializer responsibilities

Serializers should:
- Validate request input
- Normalize primitive values
- Serialize response output
- Provide clear API contracts

Serializers should not:
- Contain business workflows
- Call queues or background workers
- Call external services
- Perform multi-model transactions
- Hide authorization decisions
- Decide ownership or tenant scope

## Prefer explicit input and output serializers

For non-trivial APIs, keep request and response serializers separate:

```python
class ResourceCreateInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)

class ResourceOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ["id", "title", "description", "created_at", "updated_at"]
```

This prevents accidentally exposing write-only or internal fields in responses, and makes the API contract explicit in both directions.

## When to use ModelSerializer

Use `ModelSerializer` when the API shape closely follows the model — for detail output, list output, simple CRUD, or admin/internal APIs.

```python
# Good: explicit field list
class ResourceOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ["id", "title", "status", "created_at"]
```

Avoid `fields = "__all__"` for public or semi-public APIs. It exposes every model field including internal ones, and silently leaks new fields when the model changes.

## When to use Serializer

Use plain `Serializer` for command endpoints, non-model inputs, filter params, and workflow actions:

```python
class ResourcePublishInputSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)
    force = serializers.BooleanField(default=False)
```

## Server-owned fields

Never allow clients to set server-owned fields. Set them in services using trusted context instead.

Fields to always protect:
- Identity: `user`, `owner`, `created_by`, `updated_by`, `approved_by`
- Scope: `tenant`, `organization`, `project`
- State: `status`, `current_version`, permission flags
- Timestamps: `created_at`, `updated_at`
- Internal metadata of any kind

## Validation placement

| Validation type | Where it belongs |
|---|---|
| Field format, length, choices | Serializer field definition |
| Field content rules (e.g. non-blank after strip) | `validate_<field>` method |
| Cross-field rules | `validate()` method |
| Rules involving current user, other objects, state | Service |
| Invariants that must hold under concurrency | Database constraint |

```python
def validate_title(self, value):
    if not value.strip():
        raise serializers.ValidationError("Title cannot be blank.")
    return value
```

Move to service when validation requires:
- Querying other objects
- Checking permissions or ownership
- Running inside a transaction
- Race-prone uniqueness checks
- State transition rules

## Avoid overriding to_representation for logic

`to_representation` is for output formatting, not business logic. Avoid using it to:
- Filter fields based on permissions
- Conditionally include data based on user context
- Perform queries

```python
# Avoid: hides logic, hard to test
def to_representation(self, instance):
    data = super().to_representation(instance)
    if self.context["request"].user.is_staff:
        data["internal_notes"] = instance.internal_notes
    return data

# Prefer: use separate serializers per context, or explicit output serializer
class ResourceStaffOutputSerializer(ResourceOutputSerializer):
    internal_notes = serializers.CharField()
```

## Nested serializers

Nested serializers are fine for read output.

For nested writes, be cautious. Prefer explicit services when nested writes:
- Create or touch multiple models
- Require ownership checks
- Need to run inside a transaction
- Have complex validation
- Trigger side effects

## SerializerMethodField

Use sparingly — only for simple derived values that require no database access.

```python
full_name = serializers.SerializerMethodField()

def get_full_name(self, obj):
    return f"{obj.first_name} {obj.last_name}"
```

Avoid using it for:
- Queries per object (causes N+1)
- Permission checks
- External service calls
- Business logic

If a field needs related data for a list endpoint, prepare it in the queryset with `select_related`, `prefetch_related`, or annotations.

## Partial update

For PATCH, make partial update semantics explicit and only allow mutable fields:

```python
class ResourceUpdateInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    # Deliberately omitting: status, owner, created_at, etc.
```

Apply changes in the service:

```python
def resource_update(*, resource, actor, data):
    for field, value in data.items():
        setattr(resource, field, value)
    resource.updated_by = actor
    resource.save(update_fields=[*data.keys(), "updated_by", "updated_at"])
    return resource
```

## Error shape

Prefer stable, field-level validation errors from DRF's default format:

```json
{
  "title": ["This field is required."],
  "status": ["\"invalid_value\" is not a valid choice."]
}
```

For machine-readable frontend error handling, add stable error codes through a project-wide convention:

```json
{
  "code": "resource_not_ready",
  "detail": "Only draft resources can be submitted for review."
}
```

Pick one convention and apply it consistently across all endpoints. Avoid returning different ad-hoc error shapes per view.
