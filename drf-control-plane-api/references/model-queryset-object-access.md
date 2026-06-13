# Model, QuerySet, Manager & Object Access Reference

## Model role

Models should define the durable data shape:

- fields
- relationships
- indexes
- constraints
- simple properties
- small local invariants

Avoid putting large workflows directly on models.

Acceptable:

```python
@property
def is_archived(self):
    return self.archived_at is not None
````

Risky:

```python
def approve_and_send_email_and_enqueue_job_and_write_audit_log(self):
    ...
```

Move complex workflows to services.

## Custom QuerySet for reusable scopes

Use custom QuerySets for reusable, chainable query logic.

Example:

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

    def with_related(self):
        return self.select_related("owner").prefetch_related("tags")
```

Then:

```python
class Resource(models.Model):
    objects = ResourceQuerySet.as_manager()
```

## QuerySet vs selector

Use QuerySet methods for small reusable scopes.

Use selectors when reads become use-case specific.

QuerySet:

```python
Resource.objects.visible_to(user).active()
```

Selector:

```python
def resource_list_for_dashboard(*, user, filters):
    qs = Resource.objects.visible_to(user).with_related()
    qs = apply_resource_filters(qs, filters=filters)
    return qs
```

## Manager guidelines

Managers are entry points for model-level queries.

Good:

```python
class ResourceManager(models.Manager.from_queryset(ResourceQuerySet)):
    pass
```

Avoid putting multi-step workflows in Managers.

## Default manager and base manager

Be careful with filtered default managers.

For soft delete, the project must intentionally decide:

```python
objects = ActiveResourceManager()
all_objects = ResourceManager()
```

Important rule:

Do not filter away rows in the base manager unless you fully understand the consequences. Related object resolution and admin/internal operations may need unfiltered access.

If using soft delete, define conventions clearly:

* Which manager is default?
* Which manager is unfiltered?
* Which manager should APIs use?
* Which manager should admin/internal jobs use?

## Object access must be scoped

Never fetch private resources with an unscoped lookup.

Bad:

```python
resource = Resource.objects.get(id=resource_id)
```

Good:

```python
resource = get_object_or_404(
    Resource.objects.visible_to(user),
    id=resource_id,
)
```

For multi-tenant APIs:

```python
resource = get_object_or_404(
    Resource.objects.for_tenant(tenant).visible_to(user),
    id=resource_id,
)
```

## List and detail visibility should match

If a user cannot see an object in list, they usually should not retrieve it by detail endpoint.

Use the same visibility base query:

```python
def get_queryset(self):
    return Resource.objects.visible_to(self.request.user)
```

## Use select_related and prefetch_related deliberately

Use `select_related` for ForeignKey and OneToOne relations that will be accessed.

Use `prefetch_related` for ManyToMany, reverse ForeignKey, and larger related sets.

Example:

```python
def resource_list(*, user):
    return (
        Resource.objects
        .visible_to(user)
        .select_related("owner", "organization")
        .prefetch_related("tags")
    )
```

Do not scatter query optimization inside serializers. If serializer reads relations, the queryset or selector should prepare them.

## Avoid N+1 queries

Watch for N+1 when serializers access:

* foreign keys
* reverse relations
* many-to-many fields
* computed properties that query the database
* `SerializerMethodField`

Fix with:

* `select_related`
* `prefetch_related`
* `Prefetch`
* annotations
* moving computed values into selector/queryset

## Constraints

Use database constraints for invariants that must hold even under concurrency.

Examples:

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

Add indexes for fields frequently used in:

* filters
* ordering
* joins
* uniqueness checks
* soft-delete filters
* tenant scoping
* status dashboards
* job polling

Example:

```python
class Meta:
    indexes = [
        models.Index(fields=["organization", "status", "-created_at"]),
    ]
```

Do not add indexes blindly. They improve reads but cost write overhead and storage.

## Model validation

Do not assume `clean()` runs automatically on `save()`.

If a service depends on model validation, call `full_clean()` explicitly or enforce the rule with database constraints and service checks.

## Transactions

Use `transaction.atomic()` for multi-step writes that must succeed or fail together.

Example:

```python
@transaction.atomic
def resource_publish(*, resource, actor):
    resource.status = Resource.Status.PUBLISHED
    resource.published_by = actor
    resource.save(update_fields=["status", "published_by", "updated_at"])
    return resource
```

## Locking

Use `select_for_update()` for race-prone state transitions.

Example:

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

## Side effects and transaction commit

If a service must enqueue a job, send an email, or call an external system after a DB write, prefer triggering the side effect after the transaction commits.

Pattern:

```python
@transaction.atomic
def resource_create(*, actor, data):
    resource = Resource.objects.create(created_by=actor, **data)

    transaction.on_commit(
        lambda: enqueue_resource_created_job(resource_id=resource.id)
    )

    return resource
```