# Challenge : un pipeline durci

5 tâches, 100 points, 50 minutes.

Le projet est dans `challenge/work`. Vous faites évoluer
`.github/workflows/ci.yml`, `.github/workflows/pr-welcome.yml` et
`threat-model.yml`, et vous créez un fichier CODEOWNERS.

### Tâche 1 : l'audit des workflows tourne et le projet passe (20 pts)

`act pull_request` est vert, zizmor ne rapporte aucune faille, et les tests
tournent.

### Tâche 2 : une pull request piégée arrête le pipeline (20 pts)

Dans une copie qui ajoute un workflow `pull_request_target` récupérant le
code de la pull request, le job échoue sur zizmor.

### Tâche 3 : une erreur de syntaxe de workflow arrête le pipeline (20 pts)

Dans une copie qui ajoute un workflow au cron impossible, le job échoue sur
actionlint.

### Tâche 4 : aucun workflow privilégié n'exécute la pull request (20 pts)

Aucun workflow sur `pull_request_target` ne récupère ni n'exécute le code
proposé, et aucun script ne contient un champ contrôlé par l'auteur de la
pull request.

### Tâche 5 : l'équipe sécurité relit les chemins sensibles (20 pts)

CODEOWNERS attribue à `@acme/security` les workflows, l'infrastructure, le
triage et le modèle de menace, donne un propriétaire au code de
l'application, et T-13 est `mitigated` avec sa preuve.
