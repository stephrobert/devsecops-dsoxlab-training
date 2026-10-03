# Challenge : mesurer la fiabilité

5 tâches, 100 points, 60 minutes.

Le projet est dans `challenge/work`. Vous faites évoluer
`.github/workflows/ci.yml` et `threat-model.yml`, et vous créez
`ops/alerts.yaml`, `ops/alerts.test.yaml`,
`ops/runbooks/notes-api-indisponible.md` et `scripts/dora.py`.

### Tâche 1 : le pipeline vérifie l'alerte et mesure la livraison (20 pts)

`act pull_request` est vert, promtool vérifie les règles, et le job écrit les
métriques DORA.

### Tâche 2 : l'alerte sonne quand le budget brûle, et seulement là (20 pts)

Avec 10 % d'erreurs, `NotesApiErrorBudgetBurn` sonne à 1h30 ; avec 1 %, elle
ne sonne jamais.

### Tâche 3 : les métriques DORA sont justes (20 pts)

Sur trois journaux fabriqués, `scripts/dora.py` rend les valeurs que donne la
définition du scénario.

### Tâche 4 : le runbook guide l'astreinte (20 pts)

Quatre sections (symptômes, diagnostic, remédiation, escalade), un retour
arrière, des commandes `kubectl` qui visent `notes-api`, et l'alerte qui
renvoie au runbook.

### Tâche 5 : une règle cassée arrête le pipeline, le modèle à jour (20 pts)

Dans une copie dont la règle ne se parse plus, le job échoue ; T-18 est
`mitigated` avec sa preuve.
