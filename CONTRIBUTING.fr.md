# Contribuer à devsecops-dsoxlab-training

**Language:** [English](./CONTRIBUTING.md) · [Français](./CONTRIBUTING.fr.md)

Ce dépôt est un **catalogue de labs** consommé par la CLI
[`dsoxlab`](https://github.com/stephrobert/dsoxlab). Les contributions sont de
nouvelles versions du fil rouge, des correctifs et des traductions. La CLI vit
dans son propre dépôt : n'ajoutez pas de code moteur ici.

## Mise en place

```bash
uv tool install dsoxlab        # la CLI (outil externe)
git clone https://github.com/stephrobert/devsecops-dsoxlab-training.git
cd devsecops-dsoxlab-training
mise install                   # act, uv et Python aux versions de mise.toml
dsoxlab validate-structure     # vérifier le contrat
```

Docker doit répondre (`docker info`) : act joue le pipeline de l'apprenant dans
l'image du runner `ubuntu-24.04`, épinglée par digest. Les premières versions
sont toutes en `runtime: shell`, sans VM ni compte cloud.

## La règle d'or : un lab s'éprouve dans les deux sens

Un test qui passe ne prouve rien tant qu'on n'a pas vu **échouer** ce qui doit
échouer. Avant de commiter un lab :

```bash
python3 scripts/verify-solutions.py --deux-sens --lab capstone/<lab>
```

Le script joue la suite du lab deux fois : sur les fixtures seules, où **aucun**
test ne doit passer, puis avec la solution de référence déchiffrée par-dessus,
où **tous** doivent passer. `scripts/valider-labs.py` l'atteste ensuite par les
vraies commandes dsoxlab, dans `validation-labs.json`.

Demandez-vous, pour chaque test : **serait-il vert si l'apprenant ne faisait
rien ?** Le fil rouge rend le piège fréquent, puisque le point de départ d'une
version est la solution de la précédente : elle sait déjà faire tout ce que les
versions d'avant demandaient. Chaque test exige donc la **nouveauté** de la
version.

Éprouvez aussi chaque test contre une solution **fautive** : un `uv sync` sans
`--locked`, un `echo "5 passed"` à la place de pytest. Le test visé doit tomber,
et lui seul.

## Ce que les tests doivent lire

Ce que le pipeline **produit**, jamais ce que le YAML contient :

```python
# NON : on relit ce que l'apprenant a écrit
assert "uv sync --locked" in workflow.read_text()

# OUI : on joue le workflow sur une copie cassée exprès, et on lit le résultat
res = jouer_act(copie_au_verrou_desynchronise, "push")
assert res.job(job) == "failure"
```

`jouer_act()` et `copie_temporaire()` sont les deux portes. Lire le YAML est un
dernier recours, et il se justifie dans le test : certaines propriétés
(`permissions:`, l'épinglage d'une action par SHA) sont dans le texte et ne
laissent aucune trace dans ce qu'act produit.

## Anatomie d'un lab

```text
labs/capstone/<lab>/
├── lab.yaml            # le contrat (id, level, runtime, fixtures, validation…)
├── lab.fr.yaml         # surcharge FR du title/description UNIQUEMENT
├── README.md / README.fr.md        # la leçon
├── scenario.md / scenario.fr.md    # la situation, l'état à atteindre, la pratique SSDF visée
├── fixtures/           # notes-api tel que la version précédente l'a laissé
└── challenge/
    ├── README.md / README.fr.md    # la mission, sans pas-à-pas
    ├── hints.yaml                  # indices en base64, trois paliers de coût
    └── tests/test_functional.py    # la preuve
solution/capstone/<lab>/            # solution de référence, chiffrée par ansible-vault
```

Il n'y a ici ni `setup.yaml` ni `cleanup.yaml` : `runtime.fixtures` déclare ce
qui est copié, en préservant les sous-répertoires, et `dsoxlab clean` retire le
répertoire de travail.

## Proposer une version

- **Partir de la solution précédente.** Les fixtures d'une version sont la
  solution déchiffrée de celle d'avant, sans rien d'autre : une correction de la
  solution V2 se reporte dans les fixtures de V3.
- **Citer la pratique SSDF mise en oeuvre**, dans les deux scénarios :
  « Pratique SSDF visée : PS.1 (libellé) » et « SSDF practice targeted: PS.1
  (label) ». `tests/test_curriculums.py` refuse un code absent de la grille ou
  un libellé qui le contredit.
- **Faire pointer `doc_url` vers la leçon française** que la version fait
  pratiquer : la CLI le lit. Les README anglais pointent vers la traduction,
  calculée par `scripts/gen_doc_url_en.py`.
- **Épingler tout ce que la solution référence** : chaque action sur le SHA de
  son commit avec la version en commentaire, chaque image par digest, et dater
  la mesure en commentaire.

## Vérifications locales avant d'ouvrir une PR

```bash
dsoxlab validate-structure                                 # le contrat meta.yml + lab.yaml
python3 scripts/verify-solutions.py --deux-sens            # chaque lab dans les deux sens
python3 -m pytest tests/ -q                                # les méta-tests du dépôt
python3 scripts/gen_doc_url_en.py <chemin du dépôt du site>  # la table des traductions
python3 scripts/gen_catalog.py                             # rafraîchir le catalogue du README
```

Le catalogue est généré à partir des vrais `lab.yaml` : lancez `gen_catalog.py`
après avoir ajouté ou renommé un lab, et `--check` pour vérifier.

## Conventions

- **Id de lab :** `<section>-<slug>`, où `<section>/<slug>` est son chemin sous
  `labs/` : `capstone-v00-pipeline-minimal` vit dans `labs/capstone/v00-pipeline-minimal`.
- **Commits :** en français, sujet factuel qui dit **ce qui a changé et
  pourquoi**, sans préfixe conventionnel. Le corps raconte ce qui a été mesuré,
  y compris les mesures jetées en route : elles valent souvent plus que le
  résultat.
- **i18n :** le fichier sans suffixe est l'anglais (langue officielle du dépôt),
  le `*.fr.md` est la traduction française. Les deux doivent dire la même chose.
- **Style :** pas d'emoji ni de tiret cadratin dans ce que l'apprenant lit. Les
  messages d'assertion enseignent : ils disent ce qui ne va pas et pourquoi, pas
  seulement ce qui était attendu.

## Pull requests

Travaillez sur une branche dédiée, gardez `dsoxlab validate-structure` vert,
écrivez une description claire et reliez la version ou l'issue traitée.
