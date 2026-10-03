# Challenge : l'admission signée

5 tâches, 100 points, 50 minutes.

Le projet est dans `challenge/work`. Vous créez les politiques dans
`deploy/policies/`, et vous faites évoluer `threat-model.yml`.

### Tâche 1 : une image signée par la plateforme est admise (20 pts)

Dans `notes-api`, une image du registre interne signée par la clé de
`deploy/signing/cosign.pub` est admise.

### Tâche 2 : une image non signée est refusée (20 pts)

Le Pod est refusé, et un Deployment qui nomme cette image l'est dès sa
création.

### Tâche 3 : une image signée par une autre clé est refusée (20 pts)

Une signature ne suffit pas : elle doit venir de la clé de la plateforme.

### Tâche 4 : une image d'un autre registre est refusée dans notes-api (20 pts)

Une image de Docker Hub est refusée dans `notes-api`, et la même image reste
admise dans `default`.

### Tâche 5 : les politiques bloquent, le modèle est à jour (20 pts)

Les politiques sont des `ValidatingPolicy` et `ImageValidatingPolicy` en
`Deny`, sans `failurePolicy: Ignore`, la clé de la plateforme y figure, et
T-15 est `mitigated` avec sa preuve.
