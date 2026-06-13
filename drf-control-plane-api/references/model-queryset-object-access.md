# Model, QuerySet, Manager & Object Access Reference

## Model role

Models define the durable data shape:
- Fields, relationships, indexes, constraints
- Simple properties and small local invariants

Keep workflows out of models. Move anything that touches multiple objects, sends signals, or enqueues jobs to a service.

```python
# Acceptable: simple derived property
@property
def is_archived(self):
    return self.archived_at is not None

# Risky: orchestration belongs in a service
def approve_and_send_email_and_enqueue_job_and_write_audit_log(self):
    ...
```

## Model validation and full_clean

`clean()` does **not** run automatically on `save()`. If a service depends on model validation, either:
- Call `full_clean()` explicitly before saving, or
- Enforce the rule with a database constraint (preferred for critical invariants)

```python
# Explicit call — risky to forget, hard to enforce across all write paths
resource.full_clean()
resource.save()

# Database constraint — enforced by the DB regardless of how the object is saved
class Meta:
    constraints = [
        models.CheckConstraint(
            check=Q(status__in=["draft", "active", "archived"]),
            name="valid_resource_status",
        ),
    ]
```

Use `full_clean()` only when the validation cannot be expressed as a DB constraint (e.g. cross-field rules that involve external lookups). Prefer constraints for anything that must hold under concurrency.

## Custom QuerySet for reusable scopes

```python
class ResourceQuerySet(models.QuerySet):
    def active(self):
        return self.filter(deleted_at__isnull=True)

    def owned_by(self, user):
        return self.filter(owner=user)

    def visible_to(self, user):
        if not user or not user.is_authenticated:
            return self.none()
        return self.owned_by(user).active()

    def for_tenant(self, tenant):
        return self.filter(organization=tenant)

    def with_related(self):
        return self.select_related("owner", "organization").prefetch_related("tags")
```

Methods should be chainable and side-effect free unless intentionally implementing a bulk update or delete.

## Managers

Managers are the entry point for model-level queries.

```python
class ResourceManager(models.Manager.from_queryset(ResourceQuerySet)):
    pass

class Resource(models.Model):
    objects = ResourceManager()
```

Avoid putting multi-step workflows in Managers.

## Soft delete manager convention

If the project uses soft delete, define the convention explicitly once and follow it everywhere:

```python
class ActiveResourceManager(models.Manager):
    """Filtered manager for API use. Excludes soft-deleted rows."""
    def get_queryset(self):
        return ResourceQuerySet(self.model, using=self._db).active()

class Resource(models.Model):
    objects = ActiveResourceManager()   # filtered — default for views and serializers
    all_objects = ResourceManager()     # unfiltered — for admin, jobs, migrations
```

**Do not filter the base manager without a clear project convention.** Django uses the default manager for related object resolution. A filtered default manager can cause silent data loss in:
- Reverse FK lookups (e.g. `user.resources.all()`)
- Admin list views
- Background jobs that process all rows
- Migrations that reference related objects

When unsure, keep `objects` unfiltered and expose scoped access through explicit QuerySet methods or a named manager.

## QuerySet vs selector

Use QuerySet methods for small reusable scopes. Use selectors for use-case specific read composition.

```python
# QuerySet method: reusable
Resource.objects.visible_to(user).active()

# Selector: use-case specific, assembles the full read shape
def resource_list_for_dashboard(*, user, filters):
    qs = Resource.objects.visible_to(user).with_related()
    qs = apply_resource_filters(qs, filters=filters)
    return qs
```

## Object access must be scoped

Never fetch private resources with an unscoped lookup.

```python
# Wrong — bypasses ownership
resource = Resource.objects.get(id=resource_id)

# Correct
resource = get_object_or_404(
    Resource.objects.visible_to(user),
    id=resource_id,
)

# Multi-tenant: chain both scopes
resource = get_object_or_404(
    Resource.objects.for_tenant(tenant).visible_to(user),
    id=resource_id,
)
```

## List and detail visibility must match

If a user cannot see an object in a list endpoint, they must not be able to retrieve it via the detail endpoint. Use the same base queryset:

```python
def get_queryset(self):
    return Resource.objects.visible_to(self.request.user)
```

## select_related and prefetch_related

Use `select_related` for ForeignKey and OneToOne relations that will be accessed. Use `prefetch_related` for ManyToMany, reverse FK, and larger related sets.

```python
def resource_list(*, user):
    return (
        Resource.objects
        .visible_to(user)
        .select_related("owner", "organization")
        .prefetch_related("tags")
    )
```

Never scatter query optimization inside serializers. If a serializer reads a relation, the queryset or selector must prepare it.

## Avoid N+1 queries

Watch for N+1 when serializers access:
- Foreign keys without `select_related`
- Reverse relations without `prefetch_related`
- Many-to-many fields
- `SerializerMethodField` that queries the database
- Computed properties that hit the DB per object

Fix with `select_related`, `prefetch_related`, `Prefetch`, annotations, or by moving computed values into the selector.

## Constraints

Use database constraints for invariants that must hold even under concurrency:

```python
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=["organization", "slug"],
            name="uniq_resource_slug_per_org",
        ),
        models.CheckConstraint(
            check=Q(status__in=["draft", "active", "archived"]),
            name="valid_resource_status",
        ),
    ]
```

Do not rely only on serializer validation for critical uniqueness or state invariants.

## Indexes

Add indexes for fields frequently used in filters, ordering, joins, soft-delete scopes, tenant scoping, or job polling:

```python
class Meta:
    indexes = [
        models.Index(fields=["organization", "status", "-created_at"]),
        models.Index(fields=["deleted_at"]),  # for soft-delete active() filter
    ]
```

Do not add indexes blindly. They improve reads but cost write overhead and storage.

## Transactions

Use `transaction.atomic()` for multi-step writes that must succeed or fail together:

```python
@transaction.atomic
def resource_publish(*, resource, actor):
    resource.status = Resource.Status.PUBLISHED
    resource.published_by = actor
    resource.save(update_fields=["status", "published_by", "updated_at"])
    return resource
```

## Locking for race-prone transitions

Use `select_for_update()` for state transitions where concurrent requests could produce invalid state:

```python
@transaction.atomic
def resource_activate(*, resource_id, actor):
    resource = (
        Resource.objects
        .select_for_update()
        .get(id=resource_id)
    )

    if resource.status != Resource.Status.READY:
        raise ResourceStateError("Resource is not ready.")

    resource.status = Resource.Status.ACTIVE
    resource.save(update_fields=["status", "updated_at"])
    return resource
```

Keep transactions short. Do not hold database locks while calling slow external services.

## Side effects after commit

If a service must enqueue a job, send email, or call an external system after a DB write, trigger the side effect after the transaction commits:

```python
@transaction.atomic
def resource_create(*, actor, data):
    resource = Resource.objects.create(created_by=actor, **data)

    transaction.on_commit(
        lambda: enqueue_resource_created_job(resource_id=resource.id)
    )

    return resource
```

This prevents the side effect from firing if the transaction rolls back.
