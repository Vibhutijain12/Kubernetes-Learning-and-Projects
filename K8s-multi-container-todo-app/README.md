 
# Kubernetes Multi-Container Todo App

A 3-tier application (Frontend → Backend API → Database) deployed on Kubernetes,
built to learn: Deployments, Services, DNS-based service discovery, ConfigMaps,
Secrets, and PersistentVolumeClaims.

---

## 1. Architecture

```
Browser
   │
   ▼
[frontend Service - NodePort]
   │
   ▼
[frontend Pods - nginx + HTML/JS]
   │  nginx proxies /api/* →
   ▼
[backend Service - ClusterIP]
   │
   ▼
[backend Pods - Flask API]
   │  connects to host "postgres" →
   ▼
[postgres Service - ClusterIP]
   │
   ▼
[postgres Pod - Postgres 16]
   │  reads/writes →
   ▼
[PersistentVolumeClaim - 1Gi]
```

Three independent components, each with its own Deployment + Service,
talking to each other over internal Kubernetes DNS instead of hardcoded IPs.

---

## 2. Project structure

```
k8s-todo-app/
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── index.html
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
│
├── k8s/
│   ├── namespace.yaml
│   ├── secret.yaml
│   ├── configmap.yaml
│   ├── postgres-pvc.yaml
│   ├── postgres-deployment.yaml
|   ├── postgres-service.yaml
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│
└── README.md
```

---

## 3. Components and what they do

### Frontend — nginx + static HTML/JS
- Serves a simple page with an input box and a todo list.
- JS calls a **relative** path `/api/todos` (not a hardcoded hostname) —
  the browser only ever talks to nginx.
- `nginx.conf` proxies anything under `/api/` to `http://backend:5000/api/`.
  This keeps cluster-internal Service names out of client-side JavaScript.

### Backend — Flask API
- Exposes `GET /api/todos` and `POST /api/todos`.
- Exposes `GET /healthz` used by readiness/liveness probes.
- Reads DB connection details from environment variables
  (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`) —
  the code has no idea whether these came from a ConfigMap or a Secret.

### Postgres — database
- Standard `postgres:16` image.
- Data directory `/var/lib/postgresql/data` is mounted from a PVC, so data
  survives Pod restarts/recreation.

---

## 4. Kubernetes concepts used — what and why

### Deployment
Manages a set of identical Pods, restarts them if they crash, and allows
rolling updates / scaling. Each tier (frontend, backend, postgres) is its
own Deployment so they can be scaled, updated, and restarted independently
— e.g. scaling backend replicas doesn't touch Postgres.

### Service
A stable network identity for a group of Pods. Pods get new IPs whenever
they restart; Services don't. Two types used here:
- **ClusterIP** (default) — only reachable from inside the cluster.
  Used for `backend` and `postgres`, since neither should be exposed
  directly to the internet.
- **NodePort** — opens a port on every cluster node, reachable from
  outside. Used for `frontend`, since a browser needs to reach it.

### DNS-based service-to-service networking
Kubernetes runs an internal DNS server. Any Service gets a DNS name
matching its `metadata.name` (e.g. `postgres`, `backend`), resolvable from
any Pod in the same namespace. Full form:
`<service>.<namespace>.svc.cluster.local`.

This is why `DB_HOST=postgres` works in the backend's env vars, and why
nginx can `proxy_pass http://backend:5000` — no hardcoded IPs anywhere,
and it keeps working even as Pods are replaced.

### ConfigMap
Stores **non-sensitive** configuration as key-value pairs, injected into
containers as environment variables (via `envFrom`/`configMapKeyRef`).
Used here for `DB_HOST`, `DB_PORT`, `DB_NAME`. Lets you change config
without rebuilding images, and keeps the same image portable across
dev/staging/prod.

### Secret
Same mechanism as ConfigMap but intended for **sensitive** data
(credentials). Values are base64-encoded (obscured, not strong
encryption by itself) but Kubernetes tooling treats Secrets differently:
`kubectl describe pod` redacts Secret values by default, RBAC can
restrict who can read Secrets separately from ConfigMaps, and real
clusters typically pair Secrets with encryption-at-rest. Used here for
`POSTGRES_USER` / `POSTGRES_PASSWORD` / `DB_USER` / `DB_PASSWORD`.

### PersistentVolumeClaim (PVC)
A request for durable storage that outlives any individual Pod.
Without it, anything written inside a container's filesystem disappears
the moment that container is recreated — catastrophic for a database.
The PVC here requests 1Gi, `ReadWriteOnce`, and is mounted into the
Postgres Pod at `/var/lib/postgresql/data`.

No manual `PersistentVolume` YAML was needed — the cluster's default
`StorageClass` **dynamically provisions** a matching PV automatically
when the PVC is created. This is how most real-world clusters work;
manually created PVs are the exception, mostly used on bare-metal or
when binding to a specific pre-existing disk.

### Readiness / Liveness probes
`readinessProbe` tells Kubernetes when a Pod is ready to receive traffic;
`livenessProbe` tells it when to restart a stuck/unhealthy Pod. Both
point at the backend's `/healthz` endpoint.

---

## 5. Commands used (end-to-end)

### Build and push images
```bash
docker build -t yourname/todo-backend:v1 ./backend
docker push yourname/todo-backend:v1

docker build -t yourname/todo-frontend:v1 ./frontend
docker push yourname/todo-frontend:v1
```

If using **kind**, load images directly into the cluster instead of pushing:
```bash
kind load docker-image yourname/todo-backend:v1 --name tws-cluster
kind load docker-image yourname/todo-frontend:v1 --name tws-cluster
```

### Create the Secret (imperative alternative to secret.yaml)
```bash
kubectl create secret generic todo-db-secret \
  --namespace todo-app \
  --from-literal=POSTGRES_USER=todo_user \
  --from-literal=POSTGRES_PASSWORD='SuperSecret123!' \
  --from-literal=DB_USER=todo_user \
  --from-literal=DB_PASSWORD='SuperSecret123!'
```

### Deploy everything
```bash
kubectl apply -f namespace.yaml
kubectl apply -f secret.yaml
kubectl apply -f configmap.yaml
kubectl apply -f postgres-pvc.yaml
kubectl apply -f postgres-service.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml

# or, all at once:
kubectl apply -f k8s-all.yaml
```

### Verify resources
```bash
kubectl get pods -n todo-app -w
kubectl get svc -n todo-app
kubectl get pvc -n todo-app
kubectl get pv
kubectl describe pvc postgres-pvc -n todo-app
```

### Check DNS resolution between Pods
```bash
kubectl exec -it deploy/backend -n todo-app -- sh -c "getent hosts postgres"
```

### Check logs
```bash
kubectl logs -f deploy/backend -n todo-app
```

### Access the app (kind cluster — NodePort not exposed to host by default)
```bash
kubectl port-forward svc/frontend -n todo-app 8080:80 --address 0.0.0.0
```
Then open `http://<ec2-public-ip>:8080` in a browser
(after opening that port in the EC2 security group).

### Test the API directly (isolates backend+DB from frontend/nginx)
```bash
curl -X POST http://localhost:8080/api/todos \
  -H "Content-Type: application/json" \
  -d '{"task": "test from curl"}'

curl http://localhost:8080/api/todos
```

### Query Postgres directly (strongest proof data is really stored)
```bash
kubectl exec -it deploy/postgres -n todo-app -- psql -U todo_user -d tododb
```
```sql
SELECT * FROM todos;
\q
```

### Prove the PVC is doing its job (kill the DB pod, confirm data survives)
```bash
kubectl delete pod -l app=postgres -n todo-app
kubectl get pods -n todo-app -w
kubectl exec -it deploy/postgres -n todo-app -- psql -U todo_user -d tododb -c "SELECT * FROM todos;"
```

### Scale a Deployment
```bash
kubectl scale deploy/backend -n todo-app --replicas=4
```

### Cleanup / teardown
```bash
kubectl delete -f k8s-all.yaml
# or
kubectl delete namespace todo-app
```

---

## 7. What this project demonstrates

- Splitting an app into independently deployable/scalable tiers
- Service-to-service communication via Kubernetes DNS (no hardcoded IPs)
- Separating non-sensitive config (ConfigMap) from credentials (Secret)
- Persisting stateful data (PVC) independent of Pod lifecycle
- Exposing only what needs to be public (NodePort) while keeping the
  database and API internal (ClusterIP)
- Debugging real cluster networking issues (kind's NodePort limitation,
  YAML indentation errors, missing debug tools in minimal images)


