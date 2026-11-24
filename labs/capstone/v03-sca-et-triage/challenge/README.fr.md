# V3 : les dépendances, ce qu'on corrige et ce qu'on assume

## Situation

Depuis V2, le pipeline arrête un secret et une injection. Il ne regarde pas
ce que le projet **installe**. Le verrou `uv.lock` fige flask et werkzeug en
3.0.3, et l'équipe vient d'ajouter une route `POST /notes/import`, qui
vérifie la signature ECDSA d'un lot de notes avec la bibliothèque `ecdsa`
0.19.1. Ces trois paquets ont des vulnérabilités publiées, et rien ne le dit.

Le répertoire `challenge/work` contient le projet tel que V2 l'a laissé, avec
la route d'import, ses tests et sa menace T-11.

Pratiques SSDF visées : RV.2 (évaluer, prioriser et corriger les vulnérabilités), PW.4 (réutiliser des composants sûrs plutôt que les réécrire).

## Objectif

1. Le pipeline lance une **analyse des dépendances** sur `uv.lock`, avant les
   tests, et elle **bloque** : une vulnérabilité connue rend le job rouge.
2. Chaque vulnérabilité qui a une **version corrigée** est corrigée : le
   paquet monte, le verrou suit, le Dockerfile aussi.
3. La vulnérabilité qui n'a **pas de correctif** est triée dans
   `osv-scanner.toml` : une raison qui se relit contre le code, et une date
   d'expiration dans les six mois.
4. Le modèle de menace dit la vérité : la menace sur les dépendances (T-08)
   passe à `mitigated`, avec sa preuve.

Le projet doit rester vert. Une copie qui retrouve le verrou de départ, ou dont
l'exception a expiré, doit le rendre rouge.

## Repères

- `ghcr.io/google/osv-scanner` tourne comme étape `docker://`, image épinglée
  par digest : `scan source -r .` lit le verrou et interroge la base OSV.
- Lancez-le d'abord sur le projet tel quel : la colonne `FIXED VERSION` dit ce
  qui se corrige, et `--` ce qui ne se corrigera pas.
- Avant d'accepter un risque, lisez l'avis : quelles fonctions sont touchées,
  et notes-api les appelle-t-elle ?
- osv-scanner lit `uv.lock`, pas la ligne `pip install` du Dockerfile.

## Vérifier

```bash
dsoxlab check capstone-v03-sca-et-triage
```

Cinq contrôles, vingt points chacun. Ils jouent votre pipeline avec act sur le
projet et sur des copies piégées, relisent le verrou, le Dockerfile, le
fichier de triage et le modèle de menace.

## Analyse des dépendances et triage

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
