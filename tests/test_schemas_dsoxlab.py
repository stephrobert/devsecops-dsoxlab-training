"""Chaque `lab.yaml` et `meta.yml` respecte le schéma publié par dsoxlab.

Les labs de ce catalogue s'écrivent à la main : la commande `dsoxlab new lab`,
qui pose un squelette conforme, n'est pas disponible depuis la session qui les
rédige. Ce test tient donc le rôle du gabarit : un champ obligatoire oublié ou
une valeur hors énumération échoue ici, pas chez l'apprenant.

Le schéma est lu dans le dépôt de la CLI (`~/Projets/dsoxlab/schemas/`) quand
il est présent, sinon le test est sauté avec la raison.

    uv run pytest tests/test_schemas_dsoxlab.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
SCHEMAS = Path.home() / "Projets" / "dsoxlab" / "schemas"

jsonschema = pytest.importorskip("jsonschema")


def _schema(nom: str) -> dict:
    chemin = SCHEMAS / nom
    if not chemin.is_file():
        pytest.skip(f"schéma absent : {chemin} (dépôt dsoxlab non cloné à côté)")
    return json.loads(chemin.read_text(encoding="utf-8"))


@pytest.mark.parametrize("lab_yaml", sorted(RACINE.glob("labs/*/lab.yaml")), ids=lambda p: p.parent.name)
def test_lab_yaml_conforme(lab_yaml: Path) -> None:
    donnees = yaml.safe_load(lab_yaml.read_text(encoding="utf-8"))
    jsonschema.validate(donnees, _schema("lab.schema.json"))
    assert donnees["id"] == lab_yaml.parent.name, "l'id du lab doit être le nom de son répertoire"


@pytest.mark.parametrize("lab_yaml", sorted(RACINE.glob("labs/*/lab.yaml")), ids=lambda p: p.parent.name)
def test_fixtures_declarees_presentes(lab_yaml: Path) -> None:
    donnees = yaml.safe_load(lab_yaml.read_text(encoding="utf-8"))
    base = lab_yaml.parent / "fixtures"
    for relatif in donnees.get("runtime", {}).get("fixtures", []):
        assert (base / relatif).is_file(), f"fixture déclarée mais absente : {base / relatif}"
    sur_disque = {str(p.relative_to(base)) for p in base.rglob("*") if p.is_file()}
    oublies = sur_disque - set(donnees.get("runtime", {}).get("fixtures", []))
    assert not oublies, f"fichiers de fixtures que dsoxlab ne copiera pas (non déclarés) : {sorted(oublies)}"


def test_meta_conforme() -> None:
    meta = RACINE / "meta.yml"
    if not meta.is_file():
        pytest.skip("meta.yml pas encore écrit")
    jsonschema.validate(yaml.safe_load(meta.read_text(encoding="utf-8")), _schema("meta.schema.json"))
