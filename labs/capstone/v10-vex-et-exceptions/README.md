# V10: VEX and dated exceptions

Eleventh version of the **common thread** of the DevSecOps course. The
notes-api pipeline now blocks at the MEDIUM threshold. What can be fixed is
fixed, what is accepted becomes a dated, reasoned exception, and a VEX
document tells the operators of the previous releases what does not concern
them.

| | |
|---|---|
| Target | your workstation: uv, Python and act (`mise install`), a **Docker** that answers |
| Duration | about 50 minutes |
| Paired lesson | [VEX: stating what is actually exploitable](https://blog.stephane-robert.info/en/docs/devsecops/supply-chain/vex/) |
| Previous | `capstone-v09-runtime-cloisonne` |
| Next | `capstone-v11-slo-et-dora` |

```bash
mise install
dsoxlab run   capstone-v10-vex-et-exceptions
cd labs/capstone/v10-vex-et-exceptions/challenge/work
act pull_request
dsoxlab check capstone-v10-vex-et-exceptions
```

The tests play your pipeline, analyse the image of the previous release with
your VEX, then replay the pipeline on a copy whose exceptions have expired.
