# Challenge : le modèle de menace

5 tâches, 100 points, 40 minutes.

Le projet est dans `challenge/work`. Vous y écrivez `threat-model.yml`, et
vous faites évoluer `.github/workflows/ci.yml`. Les tests lisent votre modèle
en le confrontant au code, et jouent votre pipeline avec act.

### Tâche 1 : le modèle est valide (20 pts)

`uv run python scripts/check_threat_model.py threat-model.yml` rend 0.

### Tâche 2 : chaque route de l'application est analysée (20 pts)

Chaque route déclarée par `src/notes_api/app.py` est le composant d'au moins
une menace, nommée comme la route.

### Tâche 3 : l'injection SQL est identifiée, et reste ouverte (20 pts)

Une menace d'altération ou de divulgation vise `GET /notes/search`, et son
statut est `open`.

### Tâche 4 : un modèle cassé rend le pipeline rouge (20 pts)

Dans une copie où une menace perd sa mitigation, le job échoue sur le
vérificateur.

### Tâche 5 : le pipeline vérifie le modèle et reste vert (20 pts)

Sur le projet tel quel, le job est vert, vérifie le modèle et lance toujours
les tests.
