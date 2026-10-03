# Journal des modifications

**Language:** [English](./CHANGELOG.md) · [Français](./CHANGELOG.fr.md)

Tous les changements notables de ce projet sont consignés dans ce fichier. Le
format s'appuie sur [Keep a Changelog](https://keepachangelog.com/).

Ce dépôt est un **catalogue de contenu**, pas une bibliothèque. Une version se
publie par un tag, qui produit une archive signée (voir
[RELEASING.fr.md](./RELEASING.fr.md)) ; l'unité qui compte reste le lab, et
pour ce catalogue, la version du fil rouge.

## [Non publié]

### Ajouté

- **Le catalogue**, sur la structure des catalogues Kubernetes, Linux et
  Terraform : contrat `meta.yml` et `meta.fr.yml`, solutions de référence
  chiffrées par ansible-vault sous `solution/`, rejeu par
  `scripts/verify-solutions.py`, méta-tests du dépôt, README bilingues dont le
  catalogue est généré.
- **La grille d'objectifs NIST SSDF 1.1** (`curriculums.yml`), relevée dans le
  PDF officiel : 19 pratiques en quatre groupes, PW.3 absente. Chaque version
  cite la pratique qu'elle met en oeuvre, et `tests/test_curriculums.py` refuse
  un code absent ou un libellé contradictoire.
- **Des liens calculés par langue.** `scripts/gen_doc_url_en.py` lit les
  `translationOf` du site, le README anglais pointe vers la traduction quand
  elle existe, et `tests/test_liens_par_langue.py` refuse un lien dans la
  mauvaise langue.
- **`verify-solutions.py --deux-sens`**, qui joue aussi chaque suite sur les
  fixtures seules et exige qu'aucun test ne passe.
- **`capstone-v00-pipeline-minimal`**, la première version du fil rouge :
  `notes-api`, un service Flask et ses cinq tests, reçoit son premier pipeline.
  Cinq contrôles joués avec act 0.2.89 : le code livré passe, pytest tourne
  réellement, un test cassé et un `uv.lock` désynchronisé rendent le pipeline
  rouge, une pull request déclenche le même contrôle. Éprouvé dans les deux
  sens, puis contre deux solutions fautives : un `uv sync` sans `--locked` perd
  le contrôle du verrou, un `echo "5 passed"` à la place de pytest en perd
  trois.
- **`capstone-v01-modele-de-menace`** : notes-api reçoit son modèle de menace
  STRIDE, vérifié par un outil de l'équipe que le pipeline lance à chaque
  push. Cinq contrôles : le modèle est valide, chaque route de `app.py` y est
  analysée, l'injection SQL de `/notes/search` y est nommée et reste ouverte,
  un modèle cassé rend le pipeline rouge, le pipeline reste vert et teste
  toujours. Éprouvé dans les deux sens, puis contre trois variantes fautives
  qui perdent chacune le seul contrôle visé (deux pour le vérificateur absent).
- **`capstone-v02-secrets-et-sast`** : gitleaks et Semgrep deviennent deux
  portes bloquantes du pipeline, l'injection de `/notes/search` est corrigée
  par une requête paramétrée, un test de régression la tente, et le modèle de
  menace la déclare traitée avec ce test comme preuve. La copie piégée ajoute
  l'injection dans une route nouvelle, que nul test ne couvre : une première
  version la réintroduisait dans `/notes/search`, où le test de régression
  rendait le pipeline rouge même avec un Semgrep qui ne bloquait pas.
- **`capstone-v03-sca-et-triage`** : osv-scanner 2.6.0 devient une porte
  bloquante sur `uv.lock`. Le point de départ ajoute une route d'import
  signée, vérifiée avec `ecdsa` : huit vulnérabilités connues, sept avec une
  version corrigée, et l'attaque Minerva (GHSA-wj6h-64fc-37mp), qui n'en a
  pas. Les sept se corrigent par montée de version, la huitième se trie dans
  `osv-scanner.toml` avec une raison vérifiable contre le code (notes-api ne
  fait que vérifier) et une date d'expiration dans les six mois ; une copie
  dont l'exception a expiré rend le pipeline rouge. Éprouvé dans les deux
  sens, puis contre quatre variantes fautives : un scanner qui ne bloque pas,
  des vulnérabilités corrigeables excusées au lieu d'être corrigées, une
  exception sans échéance proche, une raison qui ne cite rien.
- **`capstone-v04-identite-sans-secret`** : le job de déploiement ne lit plus
  de clé d'accès AWS dans les secrets du dépôt. Il obtient un jeton OIDC, seul
  job autorisé à le faire, sur un push sur main uniquement, et endosse un rôle
  dont la politique de confiance vit dans un fichier JSON. Les contrôles
  évaluent cette politique contre cinq jetons (main, branche de travail, pull
  request, autre dépôt, autre audience), parce qu'act ne sait pas fournir de
  jeton OIDC : mesuré avec configure-aws-credentials v6.3.0, un rôle et une
  clé statique échouent de la même façon sous act. Le point de départ referme
  l'exception Minerva de V3 comme sa revue le prévoyait, en passant la
  vérification de signature à `cryptography`. Éprouvé dans les deux sens, puis
  contre quatre variantes fautives qui perdent chacune le seul contrôle visé.
- **`capstone-v05-pipeline-durci`** : le pipeline audite chaque workflow avant
  les tests, actionlint 1.7.12 pour la syntaxe puis zizmor 1.30.1 pour la
  sécurité, tous deux bloquants. Un workflow d'accueil sur
  `pull_request_target`, qui récupérait et exécutait le code proposé et
  collait le titre dans un script, est réécrit pour ne rien exécuter de la
  pull request ; CODEOWNERS, évalué comme GitHub le fait (la dernière ligne
  l'emporte), confie les workflows, l'infrastructure et les décisions de
  sécurité à `@acme/security`. La copie piégée est une pull request que seul
  zizmor voit : une première version employait une injection de template,
  qu'actionlint signale aussi, et le pipeline devenait rouge même avec un
  zizmor qui ne bloquait pas. Éprouvé dans les deux sens, puis contre quatre
  variantes fautives.
- **`capstone-v06-image-et-iac`** : Trivy 0.75.0 (signature vérifiée avec
  cosign, loin des versions 0.69.4 à 0.69.6 compromises en mars 2026) analyse
  la configuration, puis l'image construite, toutes deux bloquantes au seuil
  HIGH et CRITICAL. Le Dockerfile passe à deux étapes depuis des bases
  épinglées, s'installe depuis `uv.lock` sans le groupe dev, applique les
  correctifs Debian publiés et tourne sous l'uid 10001 ; l'infrastructure
  perd SSH, ferme l'API à Internet, bloque l'accès public aux buckets et les
  chiffre avec une clé KMS en rotation. Mesuré le 2026-10-03 : l'image
  python:3.12-slim du jour portait déjà une CVE HIGH de libpcre2 corrigée
  dans Debian, d'où la reconstruction avec les correctifs et
  `--ignore-unfixed`. Éprouvé dans les deux sens, puis contre quatre
  variantes fautives.
- **`tests/test_fixtures_declarees.py`** : chaque fichier de `fixtures/` doit
  être déclaré dans `runtime.fixtures`. Le `lab.yaml` de V5 omettait
  `infra/github-oidc-trust.json` : le rejeu des solutions copie le dossier
  entier et ne le voyait pas, alors qu'un apprenant lancé par `dsoxlab run`
  aurait reçu un projet dont le modèle de menace échoue d'emblée.
- **`infra/main.tf` passe `terraform validate`** dès V0 : la description
  « SSH d'administration » portait une apostrophe que le provider AWS refuse.
