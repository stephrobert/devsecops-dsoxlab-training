# V0 : le pipeline minimal

Premier lab du **fil rouge** de la formation DevSecOps : l'apprenant fait
évoluer un seul projet, `notes-api`, de V0 à V11. Ici, le projet reçoit son
premier pipeline : dépendances verrouillées, tests, à chaque push et à chaque
pull request.

| | |
|---|---|
| Cible | votre poste : uv, Python et act (`mise install`), **Docker** qui répond |
| Durée | environ 30 minutes |
| Leçon jumelée | [Le fil rouge DevSecOps](https://blog.stephane-robert.info/docs/devops/implementation/projets-fil-rouge-devsecops/) |
| Suivant | `capstone-v01-modele-de-menace` |

```bash
mise install                         # uv, Python et act
dsoxlab run capstone-v00-pipeline-minimal
cd labs/v00-pipeline-minimal/challenge/work
act push                             # joue votre workflow
dsoxlab check capstone-v00-pipeline-minimal
```

act joue le workflow dans l'image du runner `ubuntu-24.04`, épinglée par
digest dans `.actrc`. Les tests rejouent votre workflow sur le projet et sur
des copies cassées exprès, et lisent le résultat du job.
