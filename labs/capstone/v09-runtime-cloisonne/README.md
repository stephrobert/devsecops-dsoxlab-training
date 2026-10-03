# V9: a contained runtime

Tenth version of the **common thread** of the DevSecOps course. notes-api now
runs under the restricted Pod Security Standard, without an API token, and
behind NetworkPolicies that only let the ingress controller in and DNS out.

| | |
|---|---|
| Target | your workstation: Docker, kind and kubectl (`mise install`) |
| Duration | about 50 minutes |
| Paired lesson | [Isolating the network with NetworkPolicies](https://blog.stephane-robert.info/en/docs/devsecops/runtime/network-policies/) |
| Previous | `capstone-v08-admission-signee` |
| Next | `capstone-v10-vex-et-exceptions` |

```bash
mise install
dsoxlab run   capstone-v09-runtime-cloisonne
cd labs/capstone/v09-runtime-cloisonne/challenge/work
dsoxlab check capstone-v09-runtime-cloisonne
```

The tests build your image, deploy it on a kind cluster with your manifests,
then measure the real traffic. The cluster is destroyed at the end.
