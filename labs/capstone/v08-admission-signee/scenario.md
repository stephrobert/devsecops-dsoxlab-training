# V8: the cluster refuses what the platform did not sign

## Situation

Everything V1 to V7 built stops at the cluster's door. The notes-api images go
to the internal registry `registry.notes.internal:5000`, where the platform
signs them with its KMS key. But the cluster checks nothing: an image pushed
by hand, an image from Docker Hub, or a tag moved after the scan start in the
`notes-api` namespace like the others. The threat model names it: T-15,
`open`.

The platform's public key is `deploy/signing/cosign.pub`. The cluster runs
**Kyverno 1.19**.

The `challenge/work` directory holds the project as V7 left it, with that
key.

SSDF practice targeted: PS.2 (provide a mechanism for verifying software release integrity).

## Goal

Write, in `deploy/policies/`, the admission policies of the `notes-api`
namespace:

1. an image from the internal registry **signed with the platform key** is
   **admitted**;
2. an **unsigned** image, or one **signed with another key**, is **refused**,
   and a Deployment that names it is refused at creation;
3. an image from **another registry** is **refused** in `notes-api`, and only
   there: the rest of the cluster is not concerned;
4. threat T-15 moves to `mitigated`, with a policy as evidence.

## Pointers

- Kyverno 1.19 deprecates `ClusterPolicy`: write an `ImageValidatingPolicy`
  for the signature, and a `ValidatingPolicy` for the registry, both in
  `policies.kyverno.io/v1`.
- The verification only runs if a validation calls `verifyImageSignatures`.
  An attestor name carries no dash: it is read in a CEL expression.
- The public key is copied into the policy (`key.data`). The internal
  registry does not record signatures in a public transparency log:
  `ctlog.insecureIgnoreTlog: true`.
- `namespaceSelector` on `kubernetes.io/metadata.name` limits a policy to one
  namespace.

## Check

```bash
dsoxlab check capstone-v08-admission-signee
```

Five checks, twenty points each. They set up a kind cluster with the internal
registry and Kyverno, apply your policies, then request the admission of
signed, unsigned and foreign images. Allow three to four minutes.
