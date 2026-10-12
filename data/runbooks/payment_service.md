# Payment Service Runbook (Sample)

This is fictional sample content for development and testing.

## Symptoms
- Payment requests return HTTP 500.
- Requests may become slow before failures increase.
- Database connection timeout messages appear in application logs.

## Initial checks
1. Confirm the time window and affected routes.
2. Check database health and connection pool saturation.
3. Compare the incident start time with recent deployments.
4. Check whether dependent services are healthy.
5. Preserve relevant logs and request IDs.

## Safety
Do not restart services, change database settings, or roll back a deployment automatically.
An engineer must review evidence and approve any production change.
