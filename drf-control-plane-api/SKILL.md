---
name: drf-control-plane-api
description: Use this skill when designing, reviewing, or refactoring Django REST Framework APIs that manage database-backed resources, permissions, workflows, state transitions, and async job triggers. Trigger this skill whenever the user is working on any DRF view, serializer, model, queryset, permission class, or API test — even if the request seems simple or isolated. Focus on thin API layers, explicit serializers, scoped object access, model/queryset correctness, and testable contracts.
---

# DRF Control Plane API

Use this skill for production Django REST Framework APIs where DRF acts as the application API boundary for resource management, authorization, workflow commands, and database-backed state.

This skill is general-purpose and not tied to any specific project.

## When to use

- DRF endpoint design, implementation, or refactor
- Serializers for create / update / list / detail / command operations
- Permissions, ownership, multi-tenant access, or object visibility
- QuerySet, Manager, model, selector, or object-access patterns
- Service-layer boundaries for business workflows
- Async job-triggering endpoints
- API tests, schema, pagination, throttling, and error shape
- Reducing fat views, fat serializers, or unsafe object lookup

## When not to use

Do not use this skill as the primary guide for:

- Pure Django template views
- FastAPI services
- Celery worker implementation details
- Database schema design unrelated to API behavior
- Authentication provider design
- Frontend API consumption

Use a more specific skill when the task is mostly about those areas.

## Core stance

DRF is the API boundary, not the business logic layer.

**Prefer:**
- Thin views
- Explicit serializers
- Scoped QuerySets
- Service functions for writes and workflows
- Selectors or QuerySet methods for reads
- Model constraints for durable invariants
- Tests for auth, permission, object access, and response contracts

**Avoid:**
- Large workflows inside views
- Business side effects inside serializers
- Unscoped object lookups
- Exposing model internals directly
- Generic ViewSets for complex command-heavy APIs
- Inconsistent response or error shapes

## Layer rule of thumb

| Question the code is answering | Where it belongs |
|---|---|
| Can this user see this object? | QuerySet / selector / permission |
| What changes should happen? | Service |
| Is this request payload valid? | Serializer |
| How does HTTP map to behavior? | View |

## Reference map

Read only the references needed for the task.

| File | Read when... |
|---|---|
| `references/architecture.md` | Deciding app structure, service/selector boundaries, or where code should live |
| `references/api-layer.md` | Choosing APIView, GenericAPIView, generic views, ViewSet, routing, pagination, filtering, response shape |
| `references/serializers.md` | Designing input/output serializers, validation, nested serializers, ModelSerializer, command serializers |
| `references/model-queryset-object-access.md` | Reviewing models, QuerySets, Managers, ownership filters, soft delete, constraints, indexes, transactions, query optimization |
| `references/async-jobs.md` | Any endpoint that triggers background processing, state transitions, or external side effects |
| `references/testing-schema-security.md` | Writing tests, reviewing security, defining OpenAPI schema, or checking production readiness |

> **Cross-reference note:** Async endpoints almost always need both `async-jobs.md` *and* `testing-schema-security.md` (for 202 test patterns). Multi-tenant APIs need both `model-queryset-object-access.md` and `testing-schema-security.md` (for cross-user access tests).

## Default workflow

When reviewing or implementing a DRF API:

1. Identify the resource or command.
2. Decide whether this is CRUD, read-only, command-style, or async.
3. Choose the smallest suitable DRF primitive.
4. Define input serializer and output serializer separately when useful.
5. Ensure object access is scoped by user/tenant/project/organization before lookup.
6. Move business writes and workflows to services.
7. Move read composition and query optimization to QuerySets or selectors.
8. Add model constraints and indexes for durable invariants.
9. Add tests for auth, permissions, ownership, validation, success response, and failure response.
10. Add or update OpenAPI schema annotations for non-trivial endpoints.

## Output expectations

**When producing code, include:**
- The view
- Serializers (input and output separately when useful)
- Service / selector if needed
- Permission / object-access pattern
- URL / router entry
- Tests or test checklist
- Schema annotations when useful

**When reviewing code, report:**
- Correctness risks
- Security / authorization risks
- Query / performance risks
- API contract issues
- Layering issues
- Suggested patch direction
