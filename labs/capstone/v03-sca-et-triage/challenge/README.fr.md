# Challenge : analyse des dépendances et triage

5 tâches, 100 points, 45 minutes.

Le projet est dans `challenge/work`. Vous faites évoluer
`.github/workflows/ci.yml`, `pyproject.toml`, `uv.lock`, `Dockerfile` et
`threat-model.yml`, et vous créez `osv-scanner.toml`.

### Tâche 1 : le pipeline analyse les dépendances et passe (20 pts)

`act push` est vert, et le job montre osv-scanner lisant `uv.lock`, puis les
tests.

### Tâche 2 : le verrou vulnérable arrête le pipeline (20 pts)

Dans une copie qui retrouve le `pyproject.toml` et le `uv.lock` de départ, le
job échoue sur l'analyse des dépendances.

### Tâche 3 : les vulnérabilités corrigeables sont corrigées (20 pts)

flask, werkzeug et ecdsa sont verrouillés à une version corrigée, le
Dockerfile installe les mêmes, et `osv-scanner.toml` n'excuse aucune
vulnérabilité qui a un correctif.

### Tâche 4 : l'exception est justifiée, datée, et le modèle à jour (20 pts)

L'attaque Minerva sur ecdsa est acceptée avec une raison qui cite la
vérification de signature, et une date d'expiration dans les six mois. La
menace T-08 est `mitigated`, avec sa preuve.

### Tâche 5 : une exception expirée rallume l'alerte (20 pts)

Dans une copie dont `ignoreUntil` est passée, le job échoue sur
GHSA-wj6h-64fc-37mp.
