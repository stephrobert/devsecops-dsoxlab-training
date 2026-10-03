# Challenge : VEX et exceptions datées

5 tâches, 100 points, 50 minutes.

Le projet est dans `challenge/work`. Vous faites évoluer
`.github/workflows/ci.yml`, `Dockerfile`, `infra/deploy.tf` et
`threat-model.yml`, et vous créez `.trivyignore.yaml` et
`security/notes-api.openvex.json`.

### Tâche 1 : le pipeline passe au seuil MEDIUM (20 pts)

`act pull_request` est vert, et les analyses bloquantes de Trivy (`config` et
`image`) portent le seuil MEDIUM.

### Tâche 2 : l'image ne contient plus pip (20 pts)

Dans l'image construite, ni le module pip ni la commande pip n'existent.

### Tâche 3 : le VEX couvre pip dans la version précédente (20 pts)

Analysée avec votre VEX, l'image précédente ne porte plus aucune
vulnérabilité de pip, et rien d'autre n'est masqué.

### Tâche 4 : une exception expirée rallume l'alerte (20 pts)

Dans une copie dont les exceptions ont expiré, le job échoue sur l'analyse de
configuration.

### Tâche 5 : chaque décision est écrite, datée, et le modèle à jour (20 pts)

Chaque exception est limitée à ses fichiers, porte une raison et une échéance
dans les six mois, le bucket des versions n'en a aucune, et T-17 est
`mitigated` avec sa preuve.
