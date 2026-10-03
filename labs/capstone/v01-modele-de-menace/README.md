# V1: the threat model

Second version of the **common thread** of the DevSecOps course. notes-api has
had a pipeline since V0; here it gets its STRIDE threat model, confronted with
the code and checked on every push.

| | |
|---|---|
| Target | your workstation: uv, Python and act (`mise install`), a **Docker** that answers |
| Duration | about 40 minutes |
| Paired lesson | [Threat modeling with STRIDE](https://blog.stephane-robert.info/en/docs/devsecops/threat-modeling/stride/) |
| Previous | `capstone-v00-pipeline-minimal` |

```bash
mise install
dsoxlab run   capstone-v01-modele-de-menace
cd labs/capstone/v01-modele-de-menace/challenge/work
uv run python scripts/check_threat_model.py threat-model.yml
act push
dsoxlab check capstone-v01-modele-de-menace
```

The starting point is the V0 solution, plus the team's checker. The tests
confront your model with the real routes of the application, then play your
pipeline on the project and on a copy with a broken model.
