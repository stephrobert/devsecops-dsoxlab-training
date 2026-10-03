# V5 : le pipeline, lui aussi, est du code à défendre

## Situation

notes-api s'ouvre aux contributions. Pour accueillir chaque pull request,
l'équipe a ajouté `pr-welcome.yml` : il lance les tests de la contribution et
remercie l'auteur par un commentaire. Comme le commentaire demande un jeton en
écriture, y compris pour un fork, le workflow tourne sur
`pull_request_target`.

Ce déclencheur s'exécute avec les droits du dépôt. Or le workflow y récupère
le code de la pull request et l'exécute : n'importe qui, en ouvrant une pull
request, fait tourner son code avec un jeton en écriture. Le titre de la pull
request est en plus collé dans le script du commentaire : un titre bien choisi
devient une commande. Le modèle de menace l'a nommée : T-13, `open`.

Rien ne relit les workflows, et une modification de `.github/` passe en revue
comme n'importe quel fichier.

Le répertoire `challenge/work` contient le projet dans cet état.

Pratique SSDF visée : PS.1 (protéger le code contre l'accès non autorisé et l'altération).

## Objectif

1. Le pipeline **audite chaque workflow** avant les tests, et chaque audit
   **bloque** : actionlint pour la syntaxe, zizmor pour les failles de
   sécurité.
2. Aucun workflow déclenché par `pull_request_target` n'**exécute** ce que la
   pull request apporte, et aucun script ne contient un champ que son auteur
   contrôle (titre, corps, nom de branche).
3. Un fichier **CODEOWNERS** impose la revue de `@acme/security` sur
   `.github/`, `infra/`, `osv-scanner.toml` et `threat-model.yml`, et donne un
   propriétaire au reste du code.
4. La menace T-13 passe à `mitigated`, avec sa preuve.

Le projet doit rester vert sur une pull request. Une copie qui ajoute un
workflow exécutant le code d'une pull request dans un déclencheur
privilégié, ou un workflow au cron impossible, doit le rendre rouge.

## Repères

- actionlint et zizmor tournent comme étapes `docker://`, images épinglées
  par digest : `rhysd/actionlint`, et `ghcr.io/zizmorcore/zizmor` avec
  `--offline`. Dans un job, la première étape qui échoue arrête les
  suivantes : l'ordre décide de ce que chaque erreur laisse voir.
- Les tests d'une contribution tournent déjà dans `ci.yml`, sur
  `pull_request`, sans secret ni jeton en écriture.
- Une suppression d'alerte zizmor s'écrit en commentaire sur la ligne visée,
  avec sa raison : `# zizmor: ignore[<règle>] <pourquoi>`.
- Dans CODEOWNERS, la **dernière** ligne qui correspond l'emporte.

## Vérifier

```bash
dsoxlab check capstone-v05-pipeline-durci
```

Cinq contrôles, vingt points chacun. Ils jouent votre pipeline avec act sur
une pull request et sur des copies piégées, relisent les workflows, et
évaluent CODEOWNERS comme GitHub le fait.
