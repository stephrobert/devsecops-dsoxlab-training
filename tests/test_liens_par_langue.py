"""Un lien vers un guide pointe sur la version dans la langue du fichier.

Le site publie la plupart des leçons de la formation DevSecOps en français ET
en anglais. Un fichier anglais qui envoie vers le guide français alors que sa
traduction existe fait lire au lecteur anglophone une page qu'il ne comprend
pas ; un fichier français qui envoie vers `/en/` fait l'inverse.

La correspondance n'est pas écrite à la main : `scripts/gen_doc_url_en.py` la
calcule depuis les `translationOf` du site, dans `scripts/doc_url_en.json`. Ce
test la confronte à chaque lien des fichiers du dépôt :

- dans un fichier anglais (`*.md` sans `.fr.`), un lien vers un guide français
  qui a une traduction est refusé, avec l'URL anglaise à mettre ;
- dans un fichier français (`*.fr.md`), un lien vers `/en/` est refusé.

Une exception, voulue : le `doc_url` des `lab.yaml` reste la leçon française,
parce que la CLI dsoxlab le lit et que le site renvoie vers sa traduction.
Le README anglais du catalogue, lui, est calculé par `scripts/gen_catalog.py`.

    uv run pytest tests/test_liens_par_langue.py -v
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
TABLE = REPO / "scripts" / "doc_url_en.json"
BLOG = "https://blog.stephane-robert.info"
RE_LIEN = re.compile(re.escape(BLOG) + r"/(?:en/)?docs/[A-Za-z0-9/_.#-]*")


def _markdown() -> list[Path]:
    exclus = (".git", ".venv", "work", "fixtures")
    return sorted(p for p in REPO.rglob("*.md") if not set(p.relative_to(REPO).parts) & set(exclus))


def _table() -> dict[str, str]:
    return json.loads(TABLE.read_text(encoding="utf-8")) if TABLE.is_file() else {}


def test_la_table_des_traductions_existe() -> None:
    assert TABLE.is_file(), (
        "scripts/doc_url_en.json est absent : lancez "
        "`python3 scripts/gen_doc_url_en.py <chemin du dépôt du site>`."
    )


@pytest.mark.parametrize("fichier", _markdown(), ids=lambda p: str(p.relative_to(REPO)))
def test_les_liens_sont_dans_la_langue_du_fichier(fichier: Path) -> None:
    francais = ".fr." in fichier.name
    table = _table()
    erreurs = []
    for lien in RE_LIEN.findall(fichier.read_text(encoding="utf-8")):
        base = lien.split("#", 1)[0]
        base = base if base.endswith("/") else base + "/"
        if francais and "/en/docs/" in base:
            erreurs.append(f"{lien} : page anglaise dans un fichier français")
        elif not francais and "/en/docs/" not in base and base in table:
            erreurs.append(f"{lien} : la traduction existe, {table[base]}")
    assert not erreurs, f"{fichier.relative_to(REPO)} :\n  " + "\n  ".join(erreurs)
