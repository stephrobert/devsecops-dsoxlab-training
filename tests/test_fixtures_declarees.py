"""Chaque fichier de `fixtures/` est déclaré dans `runtime.fixtures`, et réciproquement.

POURQUOI CE MODULE EXISTE

Le point de départ d'un lab a lui aussi deux descriptions. Le dossier
`fixtures/` contient les fichiers ; la liste `runtime.fixtures` du `lab.yaml`
dit lesquels `dsoxlab run` copie dans `challenge/work`. Le rejeu des solutions
copie le dossier entier : il ne voit donc jamais un fichier oublié dans la
liste.

Le fil rouge l'a payé le 2026-10-03. Le `lab.yaml` de V5, dérivé de celui de
V4, ne déclarait pas `infra/github-oidc-trust.json`, que la solution de V4
venait d'ajouter. La solution de V5 passait au rejeu, et un apprenant lancé
par `dsoxlab run` aurait reçu un projet sans ce fichier : le modèle de menace,
qui le cite comme preuve de T-12, rendait son pipeline rouge avant même la
première modification.

Le contrôle compare les deux, dans les deux sens :

- un fichier présent mais non déclaré n'atteint jamais l'apprenant ;
- un fichier déclaré mais absent fait échouer `dsoxlab run`.

    pytest tests/test_fixtures_declarees.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "scripts"))
from lecture_yaml import lire_yaml  # noqa: E402

LABS = sorted(p.parent for p in (RACINE / "labs").rglob("lab.yaml"))


@pytest.mark.parametrize("lab", LABS, ids=lambda p: str(p.relative_to(RACINE / "labs")))
def test_les_fixtures_declarees_sont_celles_du_dossier(lab: Path) -> None:
    runtime = (lire_yaml(lab / "lab.yaml") or {}).get("runtime") or {}
    declarees = set(runtime.get("fixtures") or [])
    dossier = lab / "fixtures"
    if not declarees and not dossier.is_dir():
        pytest.skip("lab sans fixtures")
    presentes = {
        str(p.relative_to(dossier))
        for p in dossier.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }
    oubliees = sorted(presentes - declarees)
    fantomes = sorted(declarees - presentes)
    assert not oubliees, (
        f"{lab.name} : fichiers de fixtures/ absents de runtime.fixtures, que "
        f"`dsoxlab run` ne copierait pas : {', '.join(oubliees)}"
    )
    assert not fantomes, (
        f"{lab.name} : runtime.fixtures déclare des fichiers absents de fixtures/ : "
        f"{', '.join(fantomes)}"
    )
