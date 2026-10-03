# V5 : un pipeline durci

Sixième version du **fil rouge** de la formation DevSecOps. Les workflows de
notes-api passent leur propre audit à chaque pull request, le workflow
d'accueil n'exécute plus le code proposé, et l'équipe sécurité relit tout
changement des chemins sensibles.

| | |
|---|---|
| Cible | votre poste : uv, Python et act (`mise install`), **Docker** qui répond |
| Durée | environ 50 minutes |
| Leçon jumelée | [Auditer ses workflows avec zizmor](https://blog.stephane-robert.info/docs/pipeline-cicd/github/securite/zizmor/) |
| Précédent | `capstone-v04-identite-sans-secret` |

```bash
mise install
dsoxlab run   capstone-v05-pipeline-durci
cd labs/capstone/v05-pipeline-durci/challenge/work
act pull_request
dsoxlab check capstone-v05-pipeline-durci
```

Les tests jouent votre pipeline sur une pull request, puis sur deux copies
piégées : l'une ajoute une pull request qui exécute son propre code avec les
droits du dépôt, l'autre un workflow au cron impossible. Chacune doit être arrêtée par le bon outil.
