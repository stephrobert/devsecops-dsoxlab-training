"""V0, le pipeline minimal : cinq contrôles, vingt points chacun.

## Ce que ces tests lisent

Ce qu'act PRODUIT en jouant le workflow de l'apprenant : le résultat du job
et les lignes écrites par chaque step. Ils ne lisent pas les commandes du
YAML : un step qui écrit « tests OK » sans lancer pytest ne passe pas.

## Chaque passage se fait sur une copie

Pour voir le pipeline échouer, une COPIE du projet est cassée : un test qui
ne passe plus, une dépendance ajoutée sans mettre à jour `uv.lock`. Le projet
de l'apprenant n'est jamais touché.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import (
    APPLICATION,
    copie_temporaire,
    exiger_workdir,
    exiger_workflows,
    jouer_act,
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)
LAB_ID = "capstone-v00-pipeline-minimal"


@pytest.fixture(scope="module")
def projet() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    exiger_workflows(WORKDIR)
    return WORKDIR


@pytest.fixture(scope="module")
def jeu_livre(projet: Path):
    """Le workflow joué une fois sur le projet tel quel, partagé par deux tests."""
    return jouer_act(projet, "push")


def _pytest_a_tourne(resultat) -> bool:
    """pytest a collecté `tests/test_app.py` ET rendu un bilan « N passed in Xs »."""
    lignes = resultat.lignes
    return any("tests/test_app.py" in ligne for ligne in lignes) and any(
        re.search(r"\b\d+ passed\b.* in [0-9.]+s", ligne) for ligne in lignes
    )


def _job(resultat) -> str:
    assert resultat.jobs, (
        "act n'a joué aucun job : soit aucun workflow ne déclare cet événement "
        "dans son `on:`, soit le fichier est invalide. `act -l` liste ce qu'act "
        "a compris de vos fichiers.\n  " + resultat.resume()
    )
    assert len(resultat.jobs) == 1, (
        "Un seul job est attendu à ce stade : il installe les dépendances puis "
        "lance les tests.\n  " + resultat.resume()
    )
    return next(iter(resultat.jobs))


def _jouer_copie(projet: Path, modifier, evenement: str = "push"):
    with copie_temporaire(projet) as copie:
        modifier(copie)
        return jouer_act(copie, evenement)


def test_le_code_livre_passe(jeu_livre) -> None:
    job = _job(jeu_livre)
    assert jeu_livre.job(job) == "success", (
        "Sur le code livré, dont les tests passent, le pipeline doit être vert.\n  "
        + jeu_livre.resume()
    )


def test_les_tests_tournent_dans_le_pipeline(jeu_livre) -> None:
    assert _pytest_a_tourne(jeu_livre), (
        "Le job ne montre pas pytest collectant `tests/test_app.py` puis rendant "
        "son bilan (« N passed in ... s ») : les "
        "tests de `tests/` ne tournent pas. Un pipeline vert qui ne teste rien "
        "ne protège rien.\n  " + jeu_livre.resume()
    )


def test_un_test_casse_rend_le_pipeline_rouge(projet: Path) -> None:
    def casser(copie: Path) -> None:
        app = copie / APPLICATION
        texte = app.read_text(encoding="utf-8")
        assert 'jsonify(status="ok")' in texte, "La route /health a changé de forme dans votre projet."
        app.write_text(texte.replace('jsonify(status="ok")', 'jsonify(status="ko")'), encoding="utf-8")

    res = _jouer_copie(projet, casser)
    job = _job(res)
    assert res.job(job) == "failure", (
        "Dans une copie où /health rend « ko », `test_health` échoue : le "
        "pipeline doit être rouge. Il est vert, donc il ne lance pas les tests, "
        "ou ignore leur échec.\n  " + res.resume()
    )


def test_un_verrou_desynchronise_rend_le_pipeline_rouge(projet: Path) -> None:
    def desynchroniser(copie: Path) -> None:
        pyproject = copie / "pyproject.toml"
        texte = pyproject.read_text(encoding="utf-8")
        assert '"werkzeug==3.0.3",' in texte, "Les dépendances de pyproject.toml ont changé de forme."
        pyproject.write_text(
            texte.replace('"werkzeug==3.0.3",', '"werkzeug==3.0.3",\n    "requests==2.32.3",'),
            encoding="utf-8",
        )

    res = _jouer_copie(projet, desynchroniser)
    job = _job(res)
    assert res.job(job) == "failure", (
        "Dans une copie où `pyproject.toml` déclare une dépendance absente de "
        "`uv.lock`, le pipeline doit refuser d'installer : la CI installe ce qui "
        "a été verrouillé et relu, pas ce qui se résout ce jour-là. Il est vert, "
        "donc il recalcule le verrou au lieu de le respecter.\n  " + res.resume()
    )


def test_une_pull_request_declenche_le_meme_controle(projet: Path) -> None:
    res = jouer_act(projet, "pull_request")
    job = _job(res)
    assert res.job(job) == "success", (
        "Une pull request doit jouer le même contrôle que le push : c'est avant "
        "la fusion qu'il sert. `act pull_request` ne joue rien de vert.\n  " + res.resume()
    )
    assert _pytest_a_tourne(res), (
        "Sur la pull request, le job est vert mais les tests ne tournent pas.\n  " + res.resume()
    )
