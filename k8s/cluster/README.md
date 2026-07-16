# Neo4j Core-Replica Cluster (REFERENCE — Neo4j Enterprise)

**Status:** `[REFERENCE]` manifests. This is the industry-correct topology from the
Scaling & Populating KG guide (Part 2 §2/§6) and `docs/sdd/10-SCALING-POPULATING-KG.md`.
It is **not** the demo's as-built runtime (the demo runs a single-node
`k8s/base/neo4j-statefulset.yaml`).

## Blockers (must resolve before this runs)

| Blocker | Why | Action |
|---------|-----|--------|
| **Neo4j Enterprise license** | Core-Replica clustering + causal consistency are **Enterprise-only**. The `neo4j:*-community` image the demo uses **cannot** form a cluster. | Obtain an Enterprise license; set `NEO4J_ACCEPT_LICENSE_AGREEMENT=yes` and use `neo4j:5-enterprise`. |
| **≥ 3 nodes** | Raft quorum needs an **odd** number of cores (3 min) on separate nodes. | A real multi-node cluster (not a single kind/minikube node) with anti-affinity. |
| **CNI with NetworkPolicy** | Heartbeat isolation (`neo4j-cluster-networkpolicy.yaml`) needs Calico/Cilium. | Ensure the cluster CNI enforces NetworkPolicy. |
| **App routing driver** | Reads must go to secondaries, writes to primaries via `neo4j://` routing. | Point `NEO4J_URI=neo4j://neo4j-cluster:7687` (routing scheme). |

## Two ways to deploy

**A) Raw manifests (this folder):**
```bash
kubectl apply -k k8s/cluster/
```

**B) Official Neo4j Helm chart (recommended for lifecycle):**
```bash
helm repo add neo4j https://helm.neo4j.com/neo4j
helm install core neo4j/neo4j -f k8s/cluster/values-neo4j-helm.yaml
```
The Helm chart / Kubernetes Operator handle cluster formation (stable identity,
Raft) correctly — prefer them over hand-rolled manifests in production.

## Files

| File | Role |
|------|------|
| `neo4j-core-statefulset.yaml` | 3 core servers (StatefulSet, per-pod PVC, anti-affinity) — write path + Raft |
| `neo4j-core-service.yaml` | Headless service for stable pod DNS (cluster discovery) |
| `neo4j-replica-deployment.yaml` | Read replicas (secondaries) — elastic read pool |
| `neo4j-read-service.yaml` | Load-balanced read endpoint for replicas |
| `neo4j-cluster-networkpolicy.yaml` | Isolate heartbeat/consensus traffic to the graph tier |
| `values-neo4j-helm.yaml` | Reference values for the official Neo4j Helm chart |
| `kustomization.yaml` | Applies the raw-manifest path |

## Honesty

Do **not** tell a buyer this cluster is live in the demo. It is a validated
reference you can deploy once the blockers above are met. The demo's real graph
is the single-node StatefulSet in `k8s/base/`.
