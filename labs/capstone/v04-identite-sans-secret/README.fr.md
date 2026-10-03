# V4 : une identité sans secret

Cinquième version du **fil rouge** de la formation DevSecOps. notes-api ne
publie plus ses versions avec une clé AWS stockée dans le dépôt : le job de
déploiement échange un jeton OIDC contre des identifiants d'une heure, pour un
rôle que seule la branche main peut endosser.

| | |
|---|---|
| Cible | votre poste : uv, Python et act (`mise install`), **Docker** qui répond |
| Durée | environ 50 minutes |
| Leçon jumelée | [OIDC : s'authentifier sans secret](https://blog.stephane-robert.info/docs/pipeline-cicd/github/securite/oidc/) |
| Précédent | `capstone-v03-sca-et-triage` |
| Suivant | `capstone-v05-pipeline-durci` |

```bash
mise install
dsoxlab run   capstone-v04-identite-sans-secret
cd labs/capstone/v04-identite-sans-secret/challenge/work
act pull_request
dsoxlab check capstone-v04-identite-sans-secret
```

Les tests jouent votre pipeline sur une branche de travail et sur une pull
request, où le déploiement ne doit pas démarrer, puis évaluent la politique de
confiance du rôle contre les jetons de cinq situations.
