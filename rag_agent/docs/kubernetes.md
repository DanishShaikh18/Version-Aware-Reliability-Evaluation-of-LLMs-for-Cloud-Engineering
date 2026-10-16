# Kubernetes: Fundamentals, kubectl, and GKE

## Metadata
- **Last verified:** 2026-10-16
- **Official sources:**
  - https://kubernetes.io/docs/home/
  - https://kubernetes.io/docs/concepts/workloads/pods/
  - https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
  - https://kubernetes.io/docs/concepts/services-networking/service/
  - https://kubernetes.io/docs/tasks/tools/
  - https://cloud.google.com/kubernetes-engine/docs
- **Version note:** Kubernetes API versions change across releases. Verify `apiVersion` fields against your cluster version.

> **Kubernetes and Google Kubernetes Engine (GKE) are not the same thing.**
> Kubernetes is the open-source container orchestration system. GKE is Google Cloud's managed Kubernetes service. GKE-specific details are in a separate section at the bottom of this document.

---

## Core Concepts

| Concept | Description |
|---|---|
| **Cluster** | A set of nodes (machines) that run containerised applications managed by Kubernetes. |
| **Node** | A worker machine (VM or physical) in the cluster. Runs Pods. |
| **Pod** | The smallest deployable unit. Wraps one or more containers that share network and storage. |
| **Deployment** | Manages a set of identical Pods; handles rolling updates and self-healing. |
| **Service** | A stable network endpoint to access a set of Pods (Pods are ephemeral; Services are stable). |
| **ConfigMap** | Stores non-sensitive configuration as key-value pairs, injectable into Pods. |
| **Secret** | Stores sensitive data (passwords, tokens). Base64-encoded; not encrypted at rest by default. |
| **Namespace** | A virtual cluster within the cluster; used to isolate resources by team or environment. |
| **ReplicaSet** | Ensures a specified number of Pod replicas are running. Managed by Deployments; rarely used directly. |

---

## Installing kubectl

`kubectl` is the Kubernetes command-line tool.

### Install with gcloud (for use with GKE)
```bash
gcloud components install kubectl
kubectl version --client
```

### Install independently (for any cluster)
Follow the official guide at https://kubernetes.io/docs/tasks/tools/

### Verify installation
```bash
kubectl version --client
# Example output:
# Client Version: v1.31.x
# Kustomize Version: vX.Y.Z
```

---

## Contexts and kubeconfig

kubectl uses a configuration file (`kubeconfig`) to store cluster credentials and context.

```bash
# View current context
kubectl config current-context

# List all contexts
kubectl config get-contexts

# Switch context
kubectl config use-context CONTEXT_NAME

# View full kubeconfig
kubectl config view

# For GKE: get credentials and set context automatically
gcloud container clusters get-credentials CLUSTER_NAME \
    --region REGION \
    --project PROJECT_ID
```

Default kubeconfig location:
- Linux/macOS: `~/.kube/config`
- Windows: `%USERPROFILE%\.kube\config`

---

## Basic Commands

### Inspect resources
```bash
# List Pods in the current namespace
kubectl get pods

# List all Pods in all namespaces
kubectl get pods --all-namespaces

# List Deployments and Services
kubectl get deployments,services

# Describe a resource (detailed view)
kubectl describe pod POD_NAME
kubectl describe deployment DEPLOYMENT_NAME
kubectl describe service SERVICE_NAME

# Get resource YAML/JSON
kubectl get deployment DEPLOYMENT_NAME -o yaml
```

### Troubleshoot workloads
```bash
# View logs from a Pod
kubectl logs POD_NAME

# Follow logs in real time
kubectl logs -f POD_NAME

# Logs from a specific container in a multi-container Pod
kubectl logs POD_NAME -c CONTAINER_NAME

# Execute a command inside a running Pod
kubectl exec -it POD_NAME -- /bin/bash

# View Pod events (useful for crash debugging)
kubectl describe pod POD_NAME | grep -A 20 Events:
```

---

## Deployment and Service YAML Example

Create a file `app.yaml` with both a Deployment and a Service:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-python-app
  labels:
    app: my-python-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-python-app
  template:
    metadata:
      labels:
        app: my-python-app
    spec:
      containers:
      - name: app
        image: python:3.12-slim              # Replace with your image
        command: ["python", "-m", "http.server", "8080"]
        ports:
        - containerPort: 8080
        env:
        - name: APP_ENV
          value: "production"
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
        readinessProbe:
          httpGet:
            path: /
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 20
---
apiVersion: v1
kind: Service
metadata:
  name: my-python-app-service
spec:
  selector:
    app: my-python-app      # Must match Deployment's Pod labels
  ports:
  - protocol: TCP
    port: 80                # Port exposed by the Service
    targetPort: 8080        # Port the container is listening on
  type: ClusterIP           # Internal only; use LoadBalancer for external access
```

### Apply the manifest
```bash
# Apply (create or update)
kubectl apply -f app.yaml

# Verify resources are running
kubectl get deployment my-python-app
kubectl get pods -l app=my-python-app
kubectl get service my-python-app-service

# Delete resources
kubectl delete -f app.yaml
```

---

## Resource Requests and Limits

```yaml
resources:
  requests:           # Minimum guaranteed resources
    cpu: "100m"       # 100 millicores = 0.1 CPU core
    memory: "128Mi"   # 128 mebibytes
  limits:             # Maximum resources the container can use
    cpu: "500m"
    memory: "512Mi"
```

**Rule:** Always set both `requests` and `limits` in production. Pods without limits can consume all node resources. Pods without requests get poor scheduling.

---

## Health Probes

```yaml
readinessProbe:     # Pod receives traffic only when ready
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10

livenessProbe:      # Kubernetes restarts the container if it fails
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 20

startupProbe:       # Gives slow-starting containers time to initialise
  httpGet:
    path: /health
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
```

---

## ConfigMaps and Secrets

### ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_ENV: "production"
  LOG_LEVEL: "info"
```

Use in a Pod:
```yaml
envFrom:
- configMapRef:
    name: app-config
```

### Secret
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
stringData:           # kubectl encodes to base64 automatically
  DB_PASSWORD: "my-secret-password"  # Placeholder — use a real secret manager in production
```

> **Security warning:** Kubernetes Secrets are only base64-encoded, not encrypted, by default. For production, use **Secret Manager** (GCP), **Vault**, or **External Secrets Operator**, and enable encryption at rest for Secrets in the cluster.

---

## Namespaces

```bash
# List namespaces
kubectl get namespaces

# Create a namespace
kubectl create namespace my-namespace

# Run commands in a specific namespace
kubectl get pods -n my-namespace
kubectl apply -f app.yaml -n my-namespace
```

---

## Service Types

| Service Type | Description |
|---|---|
| `ClusterIP` | Default. Internal IP only. Accessible within the cluster. |
| `NodePort` | Exposes the service on each node's IP at a static port. |
| `LoadBalancer` | Creates an external cloud load balancer (GKE creates a GCP Load Balancer). |
| `ExternalName` | Maps a Service to an external DNS name. |

---

## Version Compatibility and Deprecated APIs

- Kubernetes deprecates and removes API versions over time. Always check `kubectl api-versions` against your cluster version.
- Common deprecated → current changes:
  - `extensions/v1beta1` → `apps/v1` for Deployments (removed in Kubernetes 1.16).
  - `networking.k8s.io/v1beta1` → `networking.k8s.io/v1` for Ingress (removed in 1.22).

```bash
# Check cluster version
kubectl version

# Check available API versions
kubectl api-versions
```

---

## GKE-Specific Details

> GKE is Google Cloud's managed Kubernetes service. These details are GKE-specific and may not apply to other Kubernetes distributions.

### Creating a GKE cluster (untested — creates billable resources)
```bash
gcloud container clusters create my-cluster \
    --region us-central1 \
    --num-nodes 3 \
    --machine-type e2-medium \
    --workload-pool=PROJECT_ID.svc.id.goog   # Enables Workload Identity
```

### Get credentials for kubectl
```bash
gcloud container clusters get-credentials my-cluster \
    --region us-central1 \
    --project PROJECT_ID
```

### GKE Autopilot (fully managed node management)
```bash
gcloud container clusters create-auto my-autopilot-cluster \
    --region us-central1
```

### Workload Identity (recommended for GKE — replaces service account keys)
Allows Pods to call GCP APIs using a Kubernetes service account mapped to a GCP service account without JSON keys.
- Documentation: https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity

### Cluster node pools
```bash
# List node pools
gcloud container node-pools list --cluster my-cluster --region us-central1
```

---

## Common Errors and Troubleshooting

| Error | Likely Cause | Fix |
|---|---|---|
| `CrashLoopBackOff` | Container crashes on start | `kubectl logs POD_NAME`; fix entrypoint or dependencies |
| `ImagePullBackOff` | Image not found or no pull credentials | Verify image name and tag; check pull secrets |
| `Pending` Pod | Insufficient node resources | Check `kubectl describe pod`; add nodes or reduce resource requests |
| `OOMKilled` | Container exceeded memory limit | Increase memory limit or optimise the application |
| `0/N nodes available` | No nodes match the scheduling constraints | Check node taints, affinities, and resource availability |

---

## Official References
- Kubernetes documentation: https://kubernetes.io/docs/home/
- Pods: https://kubernetes.io/docs/concepts/workloads/pods/
- Deployments: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- Services: https://kubernetes.io/docs/concepts/services-networking/service/
- Install kubectl: https://kubernetes.io/docs/tasks/tools/
- GKE documentation: https://cloud.google.com/kubernetes-engine/docs
- GKE Workload Identity: https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity
