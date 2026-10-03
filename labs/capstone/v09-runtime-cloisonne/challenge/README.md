# Challenge: a contained runtime

5 tasks, 100 points, 50 minutes.

The project is in `challenge/work`. You evolve `deploy/k8s/namespace.yaml`,
`deploy/k8s/deployment.yaml` and `threat-model.yml`, and you write the
NetworkPolicies in `deploy/k8s/`.

### Task 1: the namespace enforces the restricted standard (20 pts)

A privileged pod is refused at admission in `notes-api`.

### Task 2: notes-api runs under the restricted standard (20 pts)

The Deployment becomes available, and the process runs without privileges,
without possible escalation and without any Linux capability.

### Task 3: only the ingress controller reaches the API (20 pts)

From `ingress`, `/health` answers; from `default`, the connection fails.

### Task 4: notes-api only goes out to DNS (20 pts)

From notes-api, DNS resolution works, and a server of `default` is
unreachable.

### Task 5: the pod carries no token, the model is up to date (20 pts)

No Kubernetes API token is mounted in the pod, and T-16 is `mitigated` with
its evidence.
