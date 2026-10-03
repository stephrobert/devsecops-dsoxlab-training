# V10 : VEX et exceptions datées

Onzième version du **fil rouge** de la formation DevSecOps. Le pipeline de
notes-api bloque désormais au seuil MEDIUM. Ce qui se corrige est corrigé, ce
qui s'accepte devient une exception datée et motivée, et un document VEX dit
aux exploitants des versions précédentes ce qui ne les concerne pas.

| | |
|---|---|
| Cible | votre poste : uv, Python et act (`mise install`), **Docker** qui répond |
| Durée | environ 50 minutes |
| Leçon jumelée | [VEX : dire ce qui est réellement exploitable](https://blog.stephane-robert.info/docs/securiser/supply-chain/vex/) |
| Précédent | `capstone-v09-runtime-cloisonne` |
| Suivant | `capstone-v11-slo-et-dora` |

```bash
mise install
dsoxlab run   capstone-v10-vex-et-exceptions
cd labs/capstone/v10-vex-et-exceptions/challenge/work
act pull_request
dsoxlab check capstone-v10-vex-et-exceptions
```

Les tests jouent votre pipeline, analysent l'image de la version précédente
avec votre VEX, puis rejouent le pipeline sur une copie dont les exceptions
ont expiré.
