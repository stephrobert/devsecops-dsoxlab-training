"""V2, secrets et SAST bloquants : cinq contrôles, vingt points chacun.

## Ce que ces tests lisent

Ce qu'act PRODUIT en jouant le pipeline de l'apprenant : le résultat du job,
et les lignes que gitleaks, Semgrep et pytest écrivent. Pour voir les portes
se fermer, une COPIE du projet reçoit un secret, ou retrouve la requête SQL
concaténée : le pipeline doit devenir rouge, et sur la bonne porte.

Le quatrième contrôle interroge l'application elle-même : l'injection doit
être corrigée dans le code, pas seulement signalée.

## Le faux secret

Il est fabriqué à l'exécution, par concaténation : aucun jeton n'apparaît en
clair dans ce dépôt, où un scanner de secrets le prendrait pour une fuite.
"""

from __future__ import annotations

import os
import re
import secrets
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
LAB_ID = "capstone-v02-secrets-et-sast"
ROUTE_VULNERABLE = (
    '    @app.get("/notes/export")\n'
    "    def exporter():\n"
    '        owner = request.args.get("owner", "")\n'
    "        lignes = db().execute(\n"
    '            "SELECT id, owner, title, body FROM notes WHERE owner = \'" + owner + "\'"\n'
    "        ).fetchall()\n"
    "        return jsonify([dict(ligne) for ligne in lignes])\n"
)


@pytest.fixture(scope="module")
def projet() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    exiger_application(WORKDIR)
    exiger_workflows(WORKDIR)
    return WORKDIR


@pytest.fixture(scope="module")
def jeu_livre(projet: Path):
    return jouer_act(projet, "push")


def _vert(res) -> bool:
    return bool(res.jobs) and all(res.job(j) == "success" for j in res.jobs)


def _rouge(res) -> bool:
    return bool(res.jobs) and any(res.job(j) == "failure" for j in res.jobs)


def _faux_jeton() -> str:
    """Un jeton au format d'un PAT GitHub, fabriqué pour le test et jamais valide."""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return "gh" + "p_" + "".join(secrets.choice(alphabet) for _ in range(36))


def test_les_deux_portes_tournent_et_le_projet_passe(jeu_livre) -> None:
    assert _vert(jeu_livre), "Sur le projet tel quel, le pipeline doit être vert.\n  " + jeu_livre.resume()
    assert any("no leaks found" in ligne for ligne in jeu_livre.lignes), (
        "Le pipeline ne montre aucune analyse de secrets (la ligne « no leaks found » "
        "de gitleaks).\n  " + jeu_livre.resume()
    )
    assert any(re.search(r"Ran \d+ rules", ligne) for ligne in jeu_livre.lignes), (
        "Le pipeline ne montre aucune analyse statique (la ligne « Ran N rules » de "
        "Semgrep).\n  " + jeu_livre.resume()
    )
    assert any(re.search(r"\b\d+ passed\b.* in [0-9.]+s", ligne) for ligne in jeu_livre.lignes), (
        "Les tests de l'application ne tournent plus dans le pipeline.\n  " + jeu_livre.resume()
    )


def test_un_secret_arrete_le_pipeline(projet: Path) -> None:
    with copie_temporaire(projet) as copie:
        (copie / "src" / "notes_api" / "config.py").write_text(
            f'GITHUB_TOKEN = "{_faux_jeton()}"\n', encoding="utf-8"
        )
        res = jouer_act(copie, "push")
    assert _rouge(res), (
        "Une copie qui embarque un jeton GitHub dans src/notes_api/config.py doit "
        "rendre le pipeline rouge : un secret ne doit jamais atteindre main.\n  " + res.resume()
    )
    assert any("leaks found" in ligne and "no leaks" not in ligne for ligne in res.lignes), (
        "Le pipeline échoue, mais pas sur l'analyse de secrets : gitleaks n'a pas "
        "écrit « leaks found ».\n  " + res.resume()
    )


def test_une_injection_sql_arrete_le_pipeline(projet: Path) -> None:
    """L'injection arrive dans une route NOUVELLE, que les tests de l'application
    ne couvrent pas : seule l'analyse statique peut arrêter le pipeline.

    Mesuré pendant la mise au point : réintroduire l'injection dans
    /notes/search faisait échouer le test de régression de l'apprenant, et le
    pipeline devenait rouge même avec un Semgrep qui ne bloquait pas.
    """
    with copie_temporaire(projet) as copie:
        app = copie / APPLICATION
        texte = app.read_text(encoding="utf-8")
        assert texte.count("    return app\n") == 1, "La fin de create_app a changé de forme."
        texte = texte.replace("    return app\n", ROUTE_VULNERABLE + "\n    return app\n")
        app.write_text(texte, encoding="utf-8")
        res = jouer_act(copie, "push")
    assert _rouge(res), (
        "Une copie qui ajoute une route /notes/export concaténant le propriétaire "
        "dans la requête SQL doit rendre le pipeline rouge : l'analyse statique doit "
        "BLOQUER, pas seulement signaler. Aucun test ne couvre cette route, seule "
        "l'analyse peut l'arrêter.\n  " + res.resume()
    )
    assert any("Code Finding" in ligne for ligne in res.lignes), (
        "Le pipeline échoue, mais pas sur l'analyse statique : Semgrep n'a rapporté "
        "aucun constat.\n  " + res.resume()
    )


def test_la_recherche_resiste_a_l_injection(projet: Path) -> None:
    script = (
        "import json, tempfile, pathlib\n"
        "from notes_api.app import create_app\n"
        "base = pathlib.Path(tempfile.mkdtemp()) / 'notes.db'\n"
        "c = create_app(base).test_client()\n"
        "c.post('/notes', json={'owner': 'alice', 'title': 'courses'})\n"
        "c.post('/notes', json={'owner': 'bob', 'title': 'secret de bob'})\n"
        "r = c.get('/notes/search', query_string={'q': \"' OR '1'='1\"})\n"
        "print(json.dumps({'statut': r.status_code, 'notes': r.get_json()}))\n"
    )
    environnement = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    environnement["PYTHONPATH"] = str(projet / "src")
    res = subprocess.run(
        ["uv", "run", "--quiet", "--directory", str(projet), "python", "-c", script],
        capture_output=True, text=True, timeout=300, check=False, env=environnement,
    )
    assert res.returncode == 0, "L'application ne démarre pas : " + (res.stdout + res.stderr)[-800:]
    resultat = yaml.safe_load(res.stdout.strip().splitlines()[-1])
    assert resultat["notes"] == [], (
        "La recherche du terme « ' OR '1'='1 » rend des notes : "
        f"{resultat['notes']}. La requête est toujours construite par concaténation, "
        "l'injection n'est pas corrigée dans le code."
    )


def test_le_modele_dit_la_menace_traitee_et_sa_preuve(projet: Path) -> None:
    modele = yaml.safe_load((projet / "threat-model.yml").read_text(encoding="utf-8"))
    visees = [
        m for m in modele.get("threats", [])
        if str(m.get("component", "")).strip().upper() == "GET /NOTES/SEARCH"
        and str(m.get("stride", "")).strip().upper() == "T"
    ]
    assert visees, "Le modèle ne porte plus la menace d'altération sur GET /notes/search."
    traitees = [m for m in visees if m.get("status") == "mitigated"]
    assert traitees, (
        "L'injection est corrigée : la menace d'altération sur GET /notes/search "
        "passe à `mitigated`. Un modèle qui dit le code plus fragile qu'il ne l'est "
        "se périme aussi sûrement qu'un modèle trop optimiste."
    )
    preuve = projet / str(traitees[0].get("evidence") or "")
    assert preuve.is_file() and "injection" in preuve.read_text(encoding="utf-8").lower(), (
        "La preuve citée doit être un fichier du projet qui démontre la correction : "
        "un test de régression qui tente l'injection, et dont le nom le dit."
    )
