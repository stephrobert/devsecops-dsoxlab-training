# Challenge : l'exécution cloisonnée

5 tâches, 100 points, 50 minutes.

Le projet est dans `challenge/work`. Vous faites évoluer
`deploy/k8s/namespace.yaml`, `deploy/k8s/deployment.yaml` et
`threat-model.yml`, et vous écrivez les NetworkPolicies dans `deploy/k8s/`.

### Tâche 1 : l'espace de noms impose le standard restricted (20 pts)

Un Pod privilégié est refusé à l'admission dans `notes-api`.

### Tâche 2 : notes-api tourne sous le standard restricted (20 pts)

Le Deployment devient disponible, et le processus tourne sans privilège,
sans escalade possible et sans aucune capacité Linux.

### Tâche 3 : seul le contrôleur d'entrée joint l'API (20 pts)

Depuis `ingress`, `/health` répond ; depuis `default`, la connexion échoue.

### Tâche 4 : notes-api ne sort que vers le DNS (20 pts)

Depuis notes-api, la résolution DNS fonctionne, et un serveur de `default`
est injoignable.

### Tâche 5 : le Pod ne porte pas de jeton, le modèle est à jour (20 pts)

Aucun jeton de l'API Kubernetes n'est monté dans le Pod, et T-16 est
`mitigated` avec sa preuve.
