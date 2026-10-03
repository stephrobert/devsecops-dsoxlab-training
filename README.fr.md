# Formation DevSecOps : le fil rouge, de V0 à V11

**Langue :** [English](./README.md) · [Français](./README.fr.md)

[![CI](https://github.com/stephrobert/devsecops-dsoxlab-training/actions/workflows/ci.yml/badge.svg)](https://github.com/stephrobert/devsecops-dsoxlab-training/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/stephrobert/devsecops-dsoxlab-training?label=OpenSSF%20Scorecard)](https://securityscorecards.dev/viewer/?uri=github.com/stephrobert/devsecops-dsoxlab-training)
[![Plumber compliance](https://score.getplumber.io/github.com/stephrobert/devsecops-dsoxlab-training.svg)](https://score.getplumber.io/github.com/stephrobert/devsecops-dsoxlab-training)
[![SLSA 3](https://slsa.dev/images/gh-badge-level3.svg)](https://slsa.dev)
[![Licence : CC BY 4.0](https://img.shields.io/badge/Licence-CC%20BY%204.0-lightgrey.svg)](./LICENSE)

Formation **DevSecOps** pratique, pilotée par la CLI
[`dsoxlab`](https://github.com/stephrobert/dsoxlab). Ce dépôt est le **capstone**
de la [formation DevSecOps](https://blog.stephane-robert.info/docs/devops/) de
blog.stephane-robert.info, écrit comme un **fil rouge** : un seul projet,
`notes-api`, durci version après version, une version par module de la
formation.

## Ce que c'est

`devsecops-dsoxlab-training` est un **dépôt de contenu**, pas une application. Il
fournit :

- un **projet unique**, `notes-api`, un petit service Flask livré avec ses
  défauts : une requête SQL concaténée, une dépendance vulnérable, un
  Dockerfile en root, un Terraform trop ouvert, aucun pipeline ;
- des **labs** dont le point de départ est la solution du précédent, de V0 (un
  pipeline minimal) à V11 (les métriques de livraison du projet) ;
- une **validation automatique** qui joue le pipeline de l'apprenant avec act
  et juge ce qu'il produit, jamais les commandes tapées ;
- une **grille d'objectifs**, le NIST SSDF : chaque version cite la pratique
  qu'elle met en oeuvre ;
- un **score** avec des indices à coût croissant.

La CLI `dsoxlab` est le point d'entrée unique : elle pose un lab, affiche
l'énoncé, valide, note et rapporte. Elle vit dans **son propre dépôt** et
s'installe **séparément**.

## Prérequis

- Python 3.11+ et [`uv`](https://docs.astral.sh/uv/)
- `git`
- **Docker qui répond** (`docker info`) : act joue le pipeline de l'apprenant
  dans l'image du runner `ubuntu-24.04`, épinglée par digest.
- **[`mise`](https://mise.jdx.dev/)**, qui pose act 0.2.89, uv et Python aux
  versions de `mise.toml` (`mise install`). Toute version d'act antérieure à
  0.2.86 est vulnérable à CVE-2026-34041 et CVE-2026-34042.

Pas de VM ni de compte cloud pour les premières versions : tout se joue sur la
machine de l'apprenant, en `runtime: shell`. Les versions qui demandent un
cluster Kubernetes ou une VM le déclareront dans leur `lab.yaml`.

## Installation

`dsoxlab` est publiée sur [PyPI](https://pypi.org/project/dsoxlab/) et s'installe
comme un outil autonome :

```bash
# 1. Installer la CLI dsoxlab (outil externe, hors de ce dépôt)
uv tool install dsoxlab        # ou : pipx install dsoxlab

# 2. Cloner ce catalogue de labs, et poser ses outils
git clone https://github.com/stephrobert/devsecops-dsoxlab-training.git
cd devsecops-dsoxlab-training
mise install

# 3. Vérifier que le contrat est valide
dsoxlab validate-structure
```

### Votre premier lab, en cinq minutes

```bash
dsoxlab list-labs                                # parcourir le catalogue
dsoxlab run       capstone-v00-pipeline-minimal  # poser l'état de départ
dsoxlab challenge capstone-v00-pipeline-minimal  # lire la mission
# ... vous travaillez dans challenge/work ...
act push                                         # jouer votre pipeline
dsoxlab check     capstone-v00-pipeline-minimal  # valider et noter
```

`run` crée le répertoire de travail du lab et y copie les fixtures déclarées.
Tout se passe ensuite dans `challenge/work` : c'est le seul endroit que vous
modifiez, et `dsoxlab clean` le retire.

Bloqué ? `dsoxlab hint <id>` révèle un indice, dont le coût est déduit du score.

### Garder à jour

```bash
git pull                       # le catalogue
uv tool upgrade dsoxlab        # le moteur
mise install                   # les outils épinglés
```

Les trois évoluent séparément. Un lab qui échoue après une montée de version
d'act ou de l'image du runner est un défaut du catalogue : ouvrez une issue, le
formulaire arrive prérempli par `dsoxlab support --issue`.

## Comment ça marche

### Le contrat déclaratif, à deux niveaux

Le catalogue est décrit par des données, pas par du code, ce qui laisse le
moteur `dsoxlab` agnostique du domaine :

- **`meta.yml`**, à la racine, déclare l'identité du dépôt et l'**ordre** des
  versions, qui est celui du jeu : il ne se réordonne pas ;
- **`lab.yaml`**, par lab, déclare ses `skills`, son `level`, son `runtime`
  (type, fixtures), ses `distros`, son `doc_url` et un bloc `validation`. Un
  `lab.fr.yaml` surcharge le `title` et la `description` en français, et rien
  d'autre.

`dsoxlab validate-structure` contrôle tout le contrat, et
`tests/test_schemas_dsoxlab.py` confronte chaque `lab.yaml` au schéma publié par
dsoxlab.

### Le cycle de vie d'un lab

```bash
dsoxlab list-labs              # parcourir le catalogue
dsoxlab show      <id>         # métadonnées et état d'un lab
dsoxlab run       <id>         # poser l'état de départ
dsoxlab challenge <id>         # lire la mission, sans pas-à-pas
dsoxlab hint      <id>         # révéler un indice (déduit du score)
dsoxlab check     <id>         # lancer les tests, calculer et enregistrer le score
dsoxlab clean     <id>         # retirer le répertoire de travail
dsoxlab progress               # avancement par section, score moyen
```

### Les runtimes

| Runtime | Ce que le lab demande |
|---|---|
| `shell` + act | un terminal, Docker et les outils de `mise.toml`. Les tests jouent votre pipeline avec act, sur votre projet et sur des copies cassées exprès. |

### Le modèle de validation

La validation **prouve l'état, elle ne fait pas confiance à l'apprenant**. Chaque
lab livre des tests `pytest` sous `challenge/tests/` qui jouent le pipeline avec
act et lisent ce qu'il produit : le résultat du job et les lignes écrites par
chaque step. Pour voir le pipeline échouer quand il doit échouer, un test
modifie une **copie** du projet : un test cassé, un secret injecté, une
dépendance vulnérable. Votre projet n'est jamais touché.

Et un lab s'éprouve **dans les deux sens** : les tests doivent échouer avant le
travail, et passer après. `scripts/verify-solutions.py --deux-sens` le vérifie
pour chaque lab, et `scripts/valider-labs.py` l'atteste par les vraies commandes
dsoxlab dans `validation-labs.json`.

Les solutions de référence vivent sous `solution/`, **chiffrées par
ansible-vault** : une solution livrée en clair gâche le lab, et git la garde pour
toujours.

### La grille d'objectifs : le NIST SSDF

Chaque version cite, dans son scénario, la pratique du NIST SSDF qu'elle met en
oeuvre : « Pratique SSDF visée : PO.3 ». `curriculums.yml` porte la grille, sa
source officielle et la date de sa dernière confrontation, et
`tests/test_curriculums.py` refuse un code absent de la grille ou un libellé qui
le contredit.

### Score, indices, avancement

`check` enregistre un score (tests réussis sur total, moins le coût des indices
révélés). Les indices sont **en base64** dans `challenge/hints.yaml`, pour qu'on
n'y accède pas en ouvrant le fichier, et leur coût croît avec leur précision.
L'historique vit dans une base SQLite **locale à ce dépôt**.

### Les liens vers les guides

Le `doc_url` d'un lab est la leçon française, parce que dsoxlab le lit. Les
liens des README sont **calculés** : `scripts/gen_doc_url_en.py` lit les
`translationOf` du site, et `scripts/gen_catalog.py` fait pointer le README
anglais vers la traduction quand elle existe. `tests/test_liens_par_langue.py`
refuse un lien dans la mauvaise langue.

## Catalogue

<!-- LABS:START -->
### Le fil rouge : notes-api de V0 à V11

| Lab (id) | Titre | Niveau | Runtime | Guide compagnon |
|---|---|---|---|---|
| `capstone-v00-pipeline-minimal` | V0, un pipeline minimal : notes-api testée à chaque push | capstone | shell | [guide](https://blog.stephane-robert.info/docs/devops/implementation/projets-fil-rouge-devsecops/) |
| `capstone-v01-modele-de-menace` | V1, un modèle de menace : STRIDE sur notes-api, vérifié par le pipeline | capstone | shell | [guide](https://blog.stephane-robert.info/docs/devops/implementation/projets-fil-rouge-devsecops/) |
| `capstone-v02-secrets-et-sast` | V2, secrets et SAST bloquants : deux portes, et l'injection corrigée | capstone | shell | [guide](https://blog.stephane-robert.info/docs/devops/implementation/projets-fil-rouge-devsecops/) |
| `capstone-v03-sca-et-triage` | V3, analyse des dépendances et triage : corriger ce qui se corrige, dater ce qui ne se corrige pas | capstone | shell | [guide](https://blog.stephane-robert.info/docs/devops/implementation/projets-fil-rouge-devsecops/) |
| `capstone-v04-identite-sans-secret` | V4, une identité sans secret : OIDC au lieu d'une clé stockée | capstone | shell | [guide](https://blog.stephane-robert.info/docs/devops/implementation/projets-fil-rouge-devsecops/) |
| `capstone-v05-pipeline-durci` | V5, un pipeline durci : workflows audités, pull requests contenues | capstone | shell | [guide](https://blog.stephane-robert.info/docs/devops/implementation/projets-fil-rouge-devsecops/) |
| `capstone-v06-image-et-iac` | V6, l'image et l'infrastructure : ce qu'on livre au-delà du code | capstone | shell | [guide](https://blog.stephane-robert.info/docs/devops/implementation/projets-fil-rouge-devsecops/) |
| `capstone-v07-sbom-et-provenance` | V7, SBOM et provenance : savoir ce qu'on livre, prouver d'où ça vient | capstone | shell | [guide](https://blog.stephane-robert.info/docs/devops/implementation/projets-fil-rouge-devsecops/) |
| `capstone-v08-admission-signee` | V8, l'admission : le cluster refuse ce que la plateforme n'a pas signé | capstone | shell | [guide](https://blog.stephane-robert.info/docs/devops/implementation/projets-fil-rouge-devsecops/) |
| `capstone-v09-runtime-cloisonne` | V9, l'exécution cloisonnée : Pods restreints et réseau fermé | capstone | shell | [guide](https://blog.stephane-robert.info/docs/devops/implementation/projets-fil-rouge-devsecops/) |
| `capstone-v10-vex-et-exceptions` | V10, VEX et exceptions datées : chaque constat accepté est écrit | capstone | shell | [guide](https://blog.stephane-robert.info/docs/devops/implementation/projets-fil-rouge-devsecops/) |
| `capstone-v11-slo-et-dora` | V11, mesurer la fiabilité : un SLO qui réveille, un runbook, les métriques DORA | capstone | shell | [guide](https://blog.stephane-robert.info/docs/devops/implementation/projets-fil-rouge-devsecops/) |

_12 labs, table générée par `scripts/gen_catalog.py`._
<!-- LABS:END -->

## Contribuer et licence

Les contributions sont bienvenues : lisez
[CONTRIBUTING.fr.md](./CONTRIBUTING.fr.md), qui décrit l'anatomie réelle d'un lab
de ce dépôt et la règle d'or, un lab s'éprouve dans les deux sens. Le
[code de conduite](./CODE_OF_CONDUCT.fr.md) s'applique à tous les échanges, et
les vulnérabilités se signalent en privé : [SECURITY.fr.md](./SECURITY.fr.md).

### Licence

Ce contenu est publié sous [Creative Commons Attribution 4.0
International](./LICENSE) (CC BY 4.0). Vous pouvez le partager et l'adapter, y
compris commercialement, à condition de citer la source.
