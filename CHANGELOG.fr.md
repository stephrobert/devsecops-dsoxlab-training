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
