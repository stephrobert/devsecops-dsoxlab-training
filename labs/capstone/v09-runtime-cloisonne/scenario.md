# V9: if notes-api falls, it falls alone

## Situation

The cluster only admits signed images (V8). What remains is what happens
**once the image is running**. The manifests of `deploy/k8s/` were written
with the default settings: the notes-api process may gain privileges, keeps
its Linux capabilities, mounts a Kubernetes API token it does not use, and its
pod reaches any other pod of the cluster. A single flaw in the application
therefore opens the whole cluster. The threat model names it: T-16, `open`.

The ingress controller runs in the `ingress` namespace: it, and it alone, must
reach notes-api.

The `challenge/work` directory holds the project as V8 left it, with those
manifests.

SSDF practice targeted: PW.9 (configure software to have secure settings by default).

## Goal

1. The `notes-api` namespace **enforces** the **restricted** Pod Security
   Standard: a privileged pod is refused there at admission.
2. The Deployment passes that standard and becomes available: an
   unprivileged process, **escalation forbidden**, **all capabilities
   dropped**, the default seccomp profile, and **no API token** mounted.
3. **NetworkPolicies** only let in the traffic coming from the `ingress`
   namespace, on the API port, and only let out the DNS requests to
   kube-dns.
4. Threat T-16 moves to `mitigated`, with its evidence.

## Pointers

- The standard is enforced by a namespace label:
  `pod-security.kubernetes.io/enforce: restricted`. A Deployment that does
  not comply is created, but its pods are refused: the ReplicaSet events say
  so.
- A NetworkPolicy isolates the pods it selects, in the direction it declares
  (`policyTypes`): everything it does not allow is refused.
- A pod that no longer resolves any name has lost its DNS egress: kube-dns
  lives in `kube-system`, with the label `k8s-app: kube-dns`, over UDP and
  TCP.
- This lab does not cover runtime detection (Falco): it requires a real
  machine, not a cluster in Docker.

## Check

```bash
dsoxlab check capstone-v09-runtime-cloisonne
```

Five checks, twenty points each. They set up a kind cluster, build your
image, apply your manifests, then measure the real traffic from the `ingress`
namespace, from `default`, and from notes-api itself. Allow three to four
minutes.
