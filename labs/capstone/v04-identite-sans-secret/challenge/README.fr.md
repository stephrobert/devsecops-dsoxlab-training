# V4 : publier sans détenir de clé

## Situation

Le pipeline de notes-api publie désormais chaque version dans le bucket
`notes-api-releases`. Pour cela, le job `deploy` lit deux secrets du dépôt,
`AWS_ACCESS_KEY_ID` et `AWS_SECRET_ACCESS_KEY` : la clé d'un utilisateur IAM
créé par `infra/deploy.tf`. Cette clé ne périme jamais. Une action compromise,
une modification malveillante du workflow ou un journal trop bavard suffisent
à la faire sortir, et elle publie alors depuis n'importe où. Le modèle de
menace la nomme : T-12, `open`.

Le job se déclenche aussi sur n'importe quel push, branche de travail
comprise.

Entre-temps, l'équipe a tenu l'engagement du triage de V3 : la vérification
de signature est passée à `cryptography`, `ecdsa` a quitté les dépendances,
et `osv-scanner.toml` ne porte plus d'exception.

Le répertoire `challenge/work` contient le projet dans cet état. Le dépôt
GitHub s'appelle `acme/notes-api`, le compte AWS `123456789012`.

Pratique SSDF visée : PO.5 (sécuriser les environnements de développement).

## Objectif

1. Le job `deploy` s'authentifie par **OIDC** : il endosse un rôle IAM, sans
   aucune clé. Aucun workflow ne lit plus de secret de dépôt.
2. Seul ce job peut demander un jeton (`id-token: write`), et il ne démarre
   que sur un **push sur main** : ni une branche de travail ni une pull request
   ne publient.
3. Dans `infra/`, l'utilisateur IAM et sa clé disparaissent au profit d'un
   fournisseur OIDC et d'un rôle. Sa **politique de confiance** vit dans un
   fichier JSON et n'accepte qu'un jeton émis pour main de `acme/notes-api`,
   à destination de STS.
4. La menace T-12 passe à `mitigated`, avec cette politique comme preuve.

## Repères

- act ne sait pas fournir de jeton OIDC : le déploiement échoue sous act
  quoi que vous écriviez. Les contrôles le savent, et jouent le pipeline sur
  une branche de travail et sur une pull request, où il ne doit pas démarrer.
- Le jeton de GitHub porte le dépôt et la référence dans sa revendication
  `sub`, par exemple `repo:acme/notes-api:ref:refs/heads/main`.
- Un joker dans une condition de confiance est une porte : demandez-vous quel
  jeton d'un autre contexte il laisserait passer.

## Vérifier

```bash
dsoxlab check capstone-v04-identite-sans-secret
```

Cinq contrôles, vingt points chacun. Ils jouent votre pipeline avec act sur une
branche et une pull request, relisent les workflows et l'infrastructure, et
évaluent votre politique de confiance contre les jetons de cinq situations.

## Une identité sans secret

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
