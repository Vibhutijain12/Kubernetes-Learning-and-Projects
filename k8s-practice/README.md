
# Kubernetes Core Concepts

This document explains fundamental building blocks of Kubernetes: what they are, why they exist, and how they relate to each other.

---

## 1. Namespace

### What it is
A **Namespace** is a way to divide a single Kubernetes cluster into multiple virtual clusters. It's a logical boundary for organizing and isolating resources (Pods, Services, Deployments, etc.).

### Why it matters
- Lets multiple teams/projects/environments (e.g., `dev`, `staging`, `prod`) share one cluster without name collisions.
- Enables scoped access control (RBAC) — you can grant permissions per namespace.
- Enables resource quotas per team/project (CPU, memory, object counts).
- Objects in different namespaces can have the same name without conflict.

### Key points
- Some resources are namespaced (Pods, Deployments, Services), others are cluster-wide (Nodes, PersistentVolumes, Namespaces themselves).
- Default namespaces that come with every cluster: `default`, `kube-system`, `kube-public`, `kube-node-lease`.
- DNS for a Service includes the namespace: `my-service.my-namespace.svc.cluster.local`.

see my [Namespace example](./namespace.yml)

---

## 2. Pod

### What it is
A **Pod** is the smallest deployable unit in Kubernetes. It represents one instance of a running process in your cluster and wraps one or more tightly coupled containers that:
- Share the same network namespace (same IP address and port space).
- Can share storage volumes.
- Are always scheduled together on the same node.

### Why it matters
- You never deploy a raw container directly in Kubernetes — you deploy it inside a Pod.
- Most Pods run a single container, but multi-container Pods (e.g., app + sidecar/logging agent) are common for tightly coupled helper processes.
- Pods are **ephemeral** — they can be created, destroyed, and replaced at any time. You rarely create Pods directly in production; controllers (like Deployments) manage them instead.

### Key points
- Each Pod gets its own cluster-internal IP address.
- If a Pod dies, it is **not** automatically rescheduled unless it's managed by a controller.
- Containers within a Pod communicate via `localhost`.

see my [Pod example](./pod.yml)

---

## 3. Deployment

### What it is
A **Deployment** is a higher-level controller that manages Pods for you. Instead of creating Pods manually, you declare the *desired state* (which image, how many replicas, update strategy) and the Deployment controller makes sure the actual state matches it.

### Why it matters
- **Self-healing**: if a Pod crashes or a node fails, the Deployment creates a replacement automatically.
- **Scaling**: easily scale the number of Pod replicas up or down.
- **Rolling updates**: deploy new versions of your app with zero downtime, and roll back if something goes wrong.
- **Declarative management**: you describe what you want; Kubernetes handles the "how."

### How it works
A Deployment doesn't manage Pods directly — it creates and manages a **ReplicaSet**, which in turn ensures the specified number of Pod replicas are running.

```
Deployment → ReplicaSet → Pods
```

### Key points
- `replicas` defines how many identical Pods should be running.
- `selector` tells the Deployment which Pods belong to it (matched via labels).
- `strategy` controls how updates roll out (`RollingUpdate` is the default, `Recreate` is the alternative).
- Rollback is built-in: `kubectl rollout undo deployment/<name>`.

see my [Deployment example](./deployment.yml)
