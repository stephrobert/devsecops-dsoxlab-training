# V6 : l'image et l'infrastructure

Septième version du **fil rouge** de la formation DevSecOps. Le pipeline de
notes-api analyse désormais ce qu'il livre au-delà du code : la configuration
du Dockerfile et du Terraform, puis l'image construite. L'image tourne sans
privilège, et l'infrastructure n'expose plus rien à Internet.

| | |
|---|---|
| Cible | votre poste : uv, Python et act (`mise install`), **Docker** qui répond |
| Durée | environ 60 minutes |
| Leçon jumelée | [Scanner image, dépendances et IaC avec Trivy](https://blog.stephane-robert.info/docs/securiser/outils/trivy/) |
| Précédent | `capstone-v05-pipeline-durci` |
| Suivant | `capstone-v07-sbom-et-provenance` |

```bash
mise install
dsoxlab run   capstone-v06-image-et-iac
cd labs/capstone/v06-image-et-iac/challenge/work
act pull_request
dsoxlab check capstone-v06-image-et-iac
```

Les tests jouent votre pipeline sur une pull request, puis sur deux copies
piégées : l'une retire le `USER` du Dockerfile, l'autre ouvre SSH au monde.
Ils construisent aussi votre image pour vérifier l'utilisateur qui l'exécute
et les versions qu'elle embarque.
