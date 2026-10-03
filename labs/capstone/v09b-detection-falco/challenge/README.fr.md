# Challenge : la détection à l'exécution

5 tâches, 100 points, 50 minutes.

Le travail se fait sur `falco-1.lab` : vous écrivez
`/etc/falco/rules.d/notes-api.yaml`.

### Tâche 1 : les règles sont valides et Falco tourne (20 pts)

Le fichier passe `falco -V` avec les règles par défaut, le service
`falco-modern-bpf` tourne, et le conteneur notes-api aussi.

### Tâche 2 : un shell dans notes-api déclenche une alerte (20 pts)

Une alerte de vos règles, de niveau WARNING au moins, cite le conteneur et
la commande lancée.

### Tâche 3 : une écriture dans le code déclenche une alerte (20 pts)

Un fichier créé sous `/app/src` déclenche une alerte de niveau ERROR au
moins, qui cite le fichier.

### Tâche 4 : l'activité normale ne déclenche rien (20 pts)

La sonde de santé de notes-api et un shell dans un autre conteneur ne
déclenchent aucune alerte de vos règles.

### Tâche 5 : les règles survivent à un redémarrage (20 pts)

Après `systemctl restart falco-modern-bpf`, le shell dans notes-api est
toujours détecté.
