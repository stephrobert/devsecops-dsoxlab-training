# V3 : analyse des dépendances et triage

Quatrième version du **fil rouge** de la formation DevSecOps. Le pipeline de
notes-api analyse désormais ce qu'il installe : les vulnérabilités corrigeables
sont corrigées, et celle qui n'a pas de correctif est acceptée par écrit, avec
une date d'expiration.

| | |
|---|---|
| Cible | votre poste : uv, Python et act (`mise install`), **Docker** qui répond |
| Durée | environ 45 minutes |
| Leçon jumelée | [SCA : les vulnérabilités des dépendances](https://blog.stephane-robert.info/docs/securiser/analyser-code/sca/) |
| Précédent | `capstone-v02-secrets-et-sast` |
| Suivant | `capstone-v04-identite-sans-secret` |

```bash
mise install
dsoxlab run   capstone-v03-sca-et-triage
cd labs/capstone/v03-sca-et-triage/challenge/work
act push
dsoxlab check capstone-v03-sca-et-triage
```

Les tests jouent votre pipeline sur le projet, puis sur deux copies piégées :
l'une retrouve le verrou vulnérable de départ, l'autre porte une exception dont
la date est passée. Une exception expirée doit rallumer l'alerte.
