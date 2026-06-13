# Architecture Reference

## Goal

Keep DRF as a clear API boundary. Keep business workflows, read composition, and database invariants in the right layers.

## Recommended app shape

For small apps, a flat module layout is acceptable:

```text
apps/<domain>/
  models.py
  services.py
  selectors.py
  serializers.py
  views.py
  urls.py
  tests.py
```

For medium and large apps, prefer packages:

```text
apps/<domain>/
  api/
    v1/
      serializers/
        __init__.py
        inputs.py
        outputs.py
        <resource>.py
      views/
        __init__.py
        <resource>.py
      urls/
        __init__.py
        <resource>.py
  models/
    __init__.py
    <resource>.py
  services/
    __init__.py
    <use_case>.py
  selectors/
    __init__.py
    <resource>.py
  permissions/
    __init__.py
    <resource>.py
  tests/
```

**When to split:** Don't package prematurely. Split a flat file when any of these are true:
- `services.py` exceeds ~200 lines or handles 3+ distinct use cases
- `models.py` has 3+ unrelated models growing independently
- `tests.py` becomes hard to navigate across resource boundaries
- Two developers are regularly editing the same file for unrelated features

## Layer responsibilities

### Models

Use models for:

- Database fields, relationships, constraints, indexes
- Simple properties and small local invariants
- State helpers that do not orchestrate workflows

```python
# Acceptable: simple derived property
@property
def is_archived(self):
    return self.archived_at is not None
```

```python
# Risky: multi-step workflow on model — move this to a service
def approve_and_send_email_and_enqueue_job(self):
    ...
```

### QuerySets

Use custom QuerySets for reusable, chainable query scopes:

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
        return self.select_related("owner").prefetch_related("tags")
```

QuerySet methods should be chainable and side-effect free unless intentionally implementing a bulk update or delete.

### Managers

Use Managers as the model entry point. Prefer:

```python
class ResourceManager(models.Manager.from_queryset(ResourceQuerySet)):
    pass

class Resource(models.Model):
    objects = ResourceManager()
```

or shorthand:

```python
class Resource(models.Model):
    objects = ResourceQuerySet.as_manager()
```

Do not put multi-step workflows in Managers.

### Soft delete manager convention

If the project uses soft delete, define the convention explicitly and stick to it:

```python
class ActiveResourceManager(models.Manager):
    def get_queryset(self):
        return ResourceQuerySet(self.model, using=self._db).active()

class Resource(models.Model):
    objects = ActiveResourceManager()     # filtered — used in views and API layer
    all_objects = ResourceManager()       # unfiltered — used in jobs, admin, migrations
```

> **Important:** Do not filter rows in the base manager unless you fully understand the consequences. Django uses the default manager for related object resolution. Filtering it away can cause silent data loss in reverse FK lookups, admin, and internal jobs. When in doubt, keep `objects` unfiltered and add a named scoped manager.

### Selectors

Use selectors for use-case specific read orchestration:

- Object access helpers for views
- List queries with filters
- Annotating and aggregating for read APIs
- Applying `select_related` and `prefetch_related` for a specific use case

```python
def resource_get_visible(*, user, resource_id):
    return get_object_or_404(
        Resource.objects.visible_to(user),
        id=resource_id,
    )

def resource_list(*, user, filters=None):
    qs = Resource.objects.visible_to(user).with_related()
    if filters:
        qs = apply_resource_filters(qs, filters=filters)
    return qs
```

### Services

Use services for writes and workflows:

- Create / update / archive / restore
- State transitions
- Multi-model writes
- Transaction boundaries
- Enqueueing async jobs (via `on_commit`)
- Audit events
- External side effects after commit

```python
@transaction.atomic
def resource_create(*, project, user, title):
    resource = Resource.objects.create(
        project=project,
        created_by=user,
        title=title,
    )
    return resource
```

## Import direction

```text
api/views  →  serializers
api/views  →  selectors
api/views  →  services
services   →  models
selectors  →  models
permissions → selectors or querysets
```

Never import upward into views from services, or into models from the API layer.
