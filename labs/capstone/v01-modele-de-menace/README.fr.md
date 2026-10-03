# V1 : le modèle de menace

Deuxième version du **fil rouge** de la formation DevSecOps. notes-api a un
pipeline depuis V0 ; elle reçoit ici son modèle de menace STRIDE, confronté au
code et vérifié à chaque push.

| | |
|---|---|
| Cible | votre poste : uv, Python et act (`mise install`), **Docker** qui répond |
| Durée | environ 40 minutes |
| Leçon jumelée | [Threat modeling avec STRIDE](https://blog.stephane-robert.info/docs/devops/fondamentaux/threat-modeling-stride/) |
| Précédent | `capstone-v00-pipeline-minimal` |
| Suivant | `capstone-v02-secrets-et-sast` |

```bash
mise install
dsoxlab run   capstone-v01-modele-de-menace
cd labs/capstone/v01-modele-de-menace/challenge/work
uv run python scripts/check_threat_model.py threat-model.yml
act push
dsoxlab check capstone-v01-modele-de-menace
```

Le point de départ est la solution de V0, plus le vérificateur de l'équipe.
Les tests confrontent votre modèle aux routes réelles de l'application, puis
jouent votre pipeline sur le projet et sur une copie au modèle cassé.
