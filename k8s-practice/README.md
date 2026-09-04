
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

---

## 4. ReplicaSet

### What it is
A **ReplicaSet** ensures that a specified number of identical Pod replicas are running at all times. If a Pod crashes or is deleted, the ReplicaSet creates a new one to replace it. If there are too many, it deletes the extras.

### Why it matters
- Provides the self-healing and scaling foundation that Deployments rely on.
- Guarantees availability — you always have the desired number of Pods running.
- In practice, you rarely create a ReplicaSet directly — you create a **Deployment**, and the Deployment automatically creates and manages a ReplicaSet for you.

### Key points
- `replicas` defines the desired number of Pods.
- `selector` (matching Pod labels) tells the ReplicaSet which Pods it's responsible for.
- Deployments manage ReplicaSets, and ReplicaSets manage Pods — this is what enables rolling updates and rollbacks (each new version gets its own ReplicaSet).

see my [ReplicaSet example](./replicaSet.yml)

--- 

## 5. DaemonSet

### What it is
A **DaemonSet** ensures that a copy of a specific Pod runs on **every node** (or a selected subset of nodes) in the cluster. As nodes are added, Pods are added to them automatically; as nodes are removed, those Pods are garbage collected.

### Why it matters
- Useful for cluster-wide "one-per-node" background tasks rather than app workloads that need a specific replica count.
- Common use cases:
  - Log collection agents (e.g., Fluentd, Filebeat)
  - Monitoring/metrics agents (e.g., Node Exporter, Datadog agent)
  - Cluster networking components (e.g., CNI plugins like Calico/Weave)
  - Storage daemons (e.g., Ceph, GlusterFS)

### Key points
- Unlike a Deployment, you don't set `replicas` — the number of Pods automatically matches the number of eligible nodes.
- Supports rolling updates, just like Deployments (`RollingUpdate` or `OnDelete` strategy).
- If a new node joins the cluster, the DaemonSet controller automatically schedules a Pod onto it.

see my [daemonSet example](./daemonSet.yml)
