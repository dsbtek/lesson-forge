# infra/kubernetes/

Kubernetes manifests / Helm chart for a production deployment (Deployments for
api + worker + web, Services, Ingress, HPA, secrets, and a managed Postgres +
Redis + object-store wiring).

Not used in Phase 1 — local development runs via `docker-compose.yml` at the repo
root. This is a later-phase deliverable.
