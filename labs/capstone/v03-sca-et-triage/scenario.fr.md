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
