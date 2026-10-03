# V8: signed admission

Ninth version of the **common thread** of the DevSecOps course. The cluster
where notes-api runs only admits images from the internal registry signed by
the platform: an unsigned image, one signed with another key or one from
another registry is refused at the door.

| | |
|---|---|
| Target | your workstation: Docker, kind, kubectl, helm and cosign (`mise install`) |
| Duration | about 50 minutes |
| Paired lesson | [Verifying artifacts at admission](https://blog.stephane-robert.info/en/docs/devsecops/runtime/kubernetes-supply-chain-security/) |
| Previous | `capstone-v07-sbom-et-provenance` |
| Next | `capstone-v09-runtime-cloisonne` |

```bash
mise install
dsoxlab run   capstone-v08-admission-signee
cd labs/capstone/v08-admission-signee/challenge/work
dsoxlab check capstone-v08-admission-signee
```

The tests set up a kind cluster with the internal registry and Kyverno, apply
your policies, then request the admission of Pods and of a Deployment,
without creating anything. The cluster is destroyed at the end.
