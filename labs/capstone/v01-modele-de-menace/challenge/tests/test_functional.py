"""V1, le modèle de menace : cinq contrôles, vingt points chacun.

## Pourquoi trois tests lisent un fichier

Un modèle de menace EST un document : il n'a pas de comportement à observer.
Les trois premiers contrôles lisent donc `threat-model.yml`, mais jamais pour
y chercher un mot attendu : ils le confrontent au CODE. Chaque route que
`src/notes_api/app.py` déclare doit y être analysée, et la requête SQL
concaténée de `/notes/search`, qu'on ne voit qu'en lisant le code, doit y être
nommée. Un modèle recopié d'un gabarit ne passe pas.

## Pourquoi deux tests jouent le pipeline

Un modèle qui n'est vérifié par rien se périme en silence. Le pipeline doit
donc le vérifier à chaque push : une copie du projet dont le modèle est cassé
doit le rendre rouge.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest
import yaml

from conftest import (
    APPLICATION,
    copie_temporaire,
    exiger_application,
    exiger_workdir,
    exiger_workflows,
    jouer_act,
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)
LAB_ID = "capstone-v01-modele-de-menace"
MODELE = "threat-model.yml"
RE_ROUTE = re.compile(r"@app\.(get|post|put|patch|delete)\(\s*[\"']([^\"']+)[\"']")


@pytest.fixture(scope="module")
def projet() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    exiger_application(WORKDIR)
    return WORKDIR


def _menaces(projet: Path) -> list[dict]:
    chemin = projet / MODELE
    if not chemin.is_file():
        pytest.fail(f"`{MODELE}` est absent de la racine du projet : c'est le modèle à écrire.", pytrace=False)
    donnees = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    menaces = donnees.get("threats") if isinstance(donnees, dict) else None
    if not isinstance(menaces, list):
        pytest.fail(f"`{MODELE}` ne porte pas de liste `threats:`.", pytrace=False)
    return [m for m in menaces if isinstance(m, dict)]


def _routes(projet: Path) -> list[str]:
    """Les routes que l'application déclare, lues dans son code : « GET /notes »."""
    code = (projet / APPLICATION).read_text(encoding="utf-8")
    return [f"{methode.upper()} {chemin}" for methode, chemin in RE_ROUTE.findall(code)]


def _normaliser(composant: str) -> str:
    return re.sub(r"\s+", " ", composant.strip().upper())


def test_le_modele_est_valide(projet: Path) -> None:
    # Le VIRTUAL_ENV de dsoxlab ne doit pas détourner uv de celui du projet.
    environnement = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    res = subprocess.run(
        ["uv", "run", "--quiet", "--directory", str(projet), "python", "scripts/check_threat_model.py", MODELE],
        capture_output=True, text=True, timeout=300, check=False, env=environnement,
    )
    assert res.returncode == 0, (
        "Le vérificateur de l'équipe refuse le modèle :\n  "
        + (res.stdout + res.stderr).strip()[-1200:]
    )


def test_chaque_route_de_l_application_est_analysee(projet: Path) -> None:
    routes = _routes(projet)
    assert routes, "Aucune route trouvée dans src/notes_api/app.py : le fichier a changé de forme."
    composants = {_normaliser(str(m.get("component") or "")) for m in _menaces(projet)}
    oubliees = [r for r in routes if _normaliser(r) not in composants]
    assert not oubliees, (
        f"Ces routes déclarées par l'application n'ont aucune menace analysée : {oubliees}. "
        "Le composant d'une menace se nomme comme la route : « GET /notes/search »."
    )


def test_l_injection_sql_est_identifiee_et_reste_ouverte(projet: Path) -> None:
    candidates = [
        m for m in _menaces(projet)
        if _normaliser(str(m.get("component") or "")) == "GET /NOTES/SEARCH"
        and str(m.get("stride") or "").strip().upper() in {"T", "I"}
    ]
    assert candidates, (
        "La route GET /notes/search construit sa requête SQL par concaténation : "
        "c'est une altération (T) ou une divulgation (I) que le modèle doit nommer. "
        "Lisez la fonction `chercher` de app.py."
    )
    assert any(str(m.get("status")) == "open" for m in candidates), (
        "La menace sur /notes/search est déclarée traitée ou acceptée, alors que "
        "le code concatène toujours la requête. Elle reste `open` tant que la "
        "version suivante ne l'a pas corrigée : un modèle qui ment sur l'état "
        "du code est pire que pas de modèle."
    )


def test_un_modele_casse_rend_le_pipeline_rouge(projet: Path) -> None:
    exiger_workflows(projet)
    with copie_temporaire(projet) as copie:
        chemin = copie / MODELE
        if not chemin.is_file():
            pytest.fail(f"`{MODELE}` est absent : rien à casser.", pytrace=False)
        donnees = yaml.safe_load(chemin.read_text(encoding="utf-8"))
        donnees["threats"][0].pop("mitigation", None)
        chemin.write_text(yaml.safe_dump(donnees, sort_keys=False, allow_unicode=True), encoding="utf-8")
        res = jouer_act(copie, "push")
    assert res.jobs and all(res.job(j) == "failure" for j in res.jobs), (
        "Dans une copie où la première menace n'a plus de mitigation, le pipeline "
        "doit être rouge : un modèle incomplet ne doit pas pouvoir atteindre main. "
        "Le vérificateur tourne-t-il dans le workflow ?\n  " + res.resume()
    )
    assert any(ligne.startswith("THREAT-MODEL:") for ligne in res.lignes), (
        "Le pipeline échoue, mais pas sur le modèle de menace : le vérificateur "
        "n'a écrit aucune ligne `THREAT-MODEL: ...`.\n  " + res.resume()
    )


def test_le_pipeline_verifie_le_modele_et_reste_vert(projet: Path) -> None:
    exiger_workflows(projet)
    res = jouer_act(projet, "push")
    assert res.jobs and all(res.job(j) == "success" for j in res.jobs), (
        "Sur le projet tel quel, le pipeline doit rester vert.\n  " + res.resume()
    )
    assert any(ligne.startswith("threat model valid:") for ligne in res.lignes), (
        "Le pipeline est vert mais ne vérifie pas le modèle de menace : aucune "
        "ligne `threat model valid: ...`.\n  " + res.resume()
    )
    assert any(re.search(r"\b\d+ passed\b.* in [0-9.]+s", ligne) for ligne in res.lignes), (
        "Le pipeline vérifie le modèle mais ne lance plus les tests de l'application.\n  "
        + res.resume()
    )
