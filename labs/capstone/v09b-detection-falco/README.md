# V9b: runtime detection

Side version of the **common thread** of the DevSecOps course, between V9 and
V10. On a real machine, notes-api runs under Falco, and its rules report a
shell opened in its container or a write into its code, without alerting on
its normal activity.

| | |
|---|---|
| Target | an Ubuntu 24.04 VM provisioned by dsoxlab (KVM or Incus) |
| Duration | about 50 minutes |
| Paired lesson | [Runtime detection with Falco](https://blog.stephane-robert.info/en/docs/devsecops/runtime/falco/) |
| Previous | `capstone-v09-runtime-cloisonne` |
| Next | `capstone-v10-vex-et-exceptions` |

```bash
dsoxlab instructor bootstrap
dsoxlab use --provider kvm
dsoxlab provision
dsoxlab run   capstone-v09b-detection-falco
dsoxlab check capstone-v09b-detection-falco
```

Falco reads the kernel's system calls: it needs a real machine, and a kind
cluster, which shares the host kernel, would prove nothing more. The tests
trigger the actions to detect themselves, and read the alerts as JSON.
