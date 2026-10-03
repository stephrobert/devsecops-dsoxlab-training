# Challenge : une identité sans secret

5 tâches, 100 points, 50 minutes.

Le projet est dans `challenge/work`. Vous faites évoluer
`.github/workflows/ci.yml`, `infra/deploy.tf` et `threat-model.yml`, et vous
créez la politique de confiance du rôle dans `infra/`.

### Tâche 1 : ni une branche ni une pull request ne déploient (20 pts)

Sur un push vers une branche de travail et sur une pull request, les tests
passent et le job de déploiement ne démarre pas.

### Tâche 2 : aucune clé statique, ni dans le pipeline ni dans l'infra (20 pts)

Aucun workflow ne lit de secret de dépôt, et `infra/` ne déclare plus
d'utilisateur IAM ni de clé d'accès.

### Tâche 3 : seul le job de déploiement obtient un jeton OIDC (20 pts)

`id-token: write` est déclaré sur ce seul job, qui endosse un rôle
(`role-to-assume`) avec une action épinglée par SHA.

### Tâche 4 : la politique de confiance n'accepte que main (20 pts)

Le rôle lit sa politique dans un fichier JSON. Évaluée contre cinq jetons,
elle n'accepte que celui d'un push sur main de `acme/notes-api` destiné à STS.

### Tâche 5 : le modèle dit la clé retirée, et sa preuve (20 pts)

La menace T-12 est `mitigated`, et sa preuve est la politique de confiance.
