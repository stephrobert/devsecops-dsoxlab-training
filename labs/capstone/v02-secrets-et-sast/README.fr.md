# V2 : secrets et SAST bloquants

Troisième version du **fil rouge** de la formation DevSecOps. Le pipeline de
notes-api gagne deux portes qui bloquent, une analyse de secrets et une
analyse statique, et l'injection SQL nommée par le modèle de menace est
corrigée.

| | |
|---|---|
| Cible | votre poste : uv, Python et act (`mise install`), **Docker** qui répond |
| Durée | environ 50 minutes |
| Leçon jumelée | [Tests de sécurité automatisés](https://blog.stephane-robert.info/docs/devops/fondamentaux/tests-securite/) |
| Précédent | `capstone-v01-modele-de-menace` |

```bash
mise install
dsoxlab run   capstone-v02-secrets-et-sast
cd labs/capstone/v02-secrets-et-sast/challenge/work
act push
dsoxlab check capstone-v02-secrets-et-sast
```

Les tests jouent votre pipeline sur le projet, puis sur deux copies piégées :
l'une embarque un jeton, l'autre ajoute une route qui concatène une valeur dans
sa requête. Aucun test de l'application ne couvre cette route : seule
l'analyse statique peut l'arrêter.
