"""V5, un pipeline durci : cinq contrôles, vingt points chacun.

## Ce que ces tests lisent

Ce qu'act PRODUIT en jouant le pipeline sur une pull request : le résultat
des jobs, et les lignes que zizmor et actionlint écrivent. Pour voir l'audit
se fermer, une COPIE du projet reçoit une pull request piégée, ou un workflow
syntaxiquement faux : le pipeline doit devenir rouge, et sur le bon outil.

Les deux autres contrôles relisent le projet : les workflows qui se
déclenchent sur pull_request_target, et le fichier CODEOWNERS, évalué comme
GitHub le fait, la dernière ligne qui correspond l'emportant.

## Pourquoi act joue pull_request

Sur un push vers main, le job de déploiement de V4 démarre, et échoue sous act
faute de jeton OIDC. Une pull request joue tout le reste du pipeline.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from conftest import (
    copie_temporaire,
    declencheurs,
    exiger_application,
    exiger_workdir,
    exiger_workflows,
    jouer_act,
    lire_workflows,
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)
LAB_ID = "capstone-v05-pipeline-durci"
EQUIPE_SECURITE = "@acme/security"
CHEMINS_SENSIBLES = [
    ".github/workflows/ci.yml",
    ".github/workflows/nouveau.yml",
    ".github/CODEOWNERS",
    "infra/deploy.tf",
    "osv-scanner.toml",
    "threat-model.yml",
]
# Ce qu'un attaquant contrôle dans une pull request : collé dans un script,
# c'est du shell qu'il écrit.
CHAMPS_ATTAQUANT = re.compile(
    r"\$\{\{\s*github\.(head_ref|event\.pull_request\.(title|body|head\.ref|head\.label))\b"
)
# Une pull request piégée que seul zizmor voit : actionlint ne trouve rien à
# redire à sa syntaxe. Mesuré pendant la mise au point : une injection de
# template (titre collé dans un script) est AUSSI signalée par actionlint, et
# rendait le pipeline rouge même avec un zizmor qui ne bloquait pas.
WORKFLOW_PWN_REQUEST = """\
name: preview

on:
  pull_request_target:
    types: [opened]

permissions:
  contents: read

jobs:
  preview:
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          ref: refs/pull/1/merge
      - run: make preview
"""
WORKFLOW_CRON_FAUX = """\
name: nightly

on:
  schedule:
    - cron: "0 25 * * *"

permissions: {}

jobs:
  rebuild:
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    steps:
      - run: echo nuit
"""


@pytest.fixture(scope="module")
def projet() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    exiger_application(WORKDIR)
    exiger_workflows(WORKDIR)
    return WORKDIR


def _vert(res) -> bool:
    return bool(res.jobs) and all(res.job(j) == "success" for j in res.jobs)


def _rouge(res) -> bool:
    return bool(res.jobs) and any(res.job(j) == "failure" for j in res.jobs)


def _avec_workflow(projet: Path, nom: str, contenu: str):
    with copie_temporaire(projet) as copie:
        (copie / ".github" / "workflows" / nom).write_text(contenu, encoding="utf-8")
        return jouer_act(copie, "pull_request")


# ── CODEOWNERS, lu comme GitHub le lit ─────────────────────────────────────


def _motif_vers_regex(motif: str) -> re.Pattern[str]:
    ancre = motif.startswith("/")
    motif = motif.lstrip("/")
    dossier = motif.endswith("/")
    motif = motif.rstrip("/")
    morceaux = []
    i = 0
    while i < len(motif):
        if motif.startswith("**", i):
            morceaux.append(".*")
            i += 2
        elif motif[i] == "*":
            morceaux.append("[^/]*")
            i += 1
        elif motif[i] == "?":
            morceaux.append("[^/]")
            i += 1
        else:
            morceaux.append(re.escape(motif[i]))
            i += 1
    corps = "".join(morceaux)
    if motif == "":
        corps = ".*"
    prefixe = "^" if ancre or "/" in motif else "^(?:.*/)?"
    suffixe = "/.*$" if dossier else "(?:/.*)?$"
    return re.compile(prefixe + corps + suffixe)


def _proprietaires(codeowners: str, chemin: str) -> list[str]:
    retenus: list[str] = []
    for brute in codeowners.splitlines():
        regle = brute.split("#", 1)[0].strip()
        if not regle:
            continue
        motif, *proprietaires = regle.split()
        if _motif_vers_regex(motif).match(chemin):
            retenus = proprietaires
    return retenus


def _codeowners(projet: Path) -> str | None:
    for emplacement in (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS"):
        if (projet / emplacement).is_file():
            return (projet / emplacement).read_text(encoding="utf-8")
    return None


# ── Les contrôles ──────────────────────────────────────────────────────────


def test_l_audit_des_workflows_tourne_et_le_projet_passe(projet: Path) -> None:
    res = jouer_act(projet, "pull_request")
    assert _vert(res), "Sur une pull request, le pipeline doit être vert.\n  " + res.resume()
    assert any("No findings to report" in ligne for ligne in res.lignes), (
        "Le pipeline ne montre aucun audit de sécurité des workflows (la ligne "
        "« No findings to report » de zizmor), ou zizmor y trouve encore des "
        "failles.\n  " + res.resume()
    )
    assert any(re.search(r"\b\d+ passed\b.* in [0-9.]+s", ligne) for ligne in res.lignes), (
        "Les tests de l'application ne tournent plus dans le pipeline.\n  " + res.resume()
    )


def test_une_pull_request_piegee_arrete_le_pipeline(projet: Path) -> None:
    res = _avec_workflow(projet, "preview.yml", WORKFLOW_PWN_REQUEST)
    assert _rouge(res), (
        "Une copie qui ajoute un workflow pull_request_target récupérant le code de la "
        "pull request doit rendre le pipeline rouge : l'audit de sécurité des workflows "
        "doit BLOQUER.\n  " + res.resume()
    )
    assert any("dangerous-triggers" in ligne for ligne in res.lignes), (
        "Le pipeline échoue, mais pas sur l'audit de sécurité : zizmor n'a pas "
        "signalé de dangerous-triggers.\n  " + res.resume()
    )


def test_une_erreur_de_syntaxe_de_workflow_arrete_le_pipeline(projet: Path) -> None:
    res = _avec_workflow(projet, "nightly.yml", WORKFLOW_CRON_FAUX)
    assert _rouge(res), (
        "Une copie qui ajoute un workflow au cron impossible (25 heures) doit rendre "
        "le pipeline rouge : GitHub ne le déclencherait jamais, sans prévenir "
        "personne.\n  " + res.resume()
    )
    assert any("CRON" in ligne for ligne in res.lignes), (
        "Le pipeline échoue, mais pas sur la vérification de syntaxe : actionlint "
        "n'a pas signalé le cron invalide.\n  " + res.resume()
    )


def test_aucun_workflow_privilegie_n_execute_la_pull_request(projet: Path) -> None:
    for fichier, workflow in lire_workflows(projet).items():
        for ident, job in (workflow.get("jobs") or {}).items():
            for pas in job.get("steps") or []:
                script = str(pas.get("run", "")) if isinstance(pas, dict) else ""
                assert not CHAMPS_ATTAQUANT.search(script), (
                    f"Le job `{ident}` de {fichier} colle un champ de la pull request "
                    "(titre, corps, branche) dans un script : c'est du shell que l'auteur "
                    "de la pull request écrit. Passez-le par une variable d'environnement."
                )
        if "pull_request_target" not in declencheurs(workflow):
            continue
        for ident, job in (workflow.get("jobs") or {}).items():
            for pas in job.get("steps") or []:
                if not isinstance(pas, dict):
                    continue
                if str(pas.get("uses", "")).startswith("actions/checkout"):
                    ref = str((pas.get("with") or {}).get("ref", ""))
                    assert not re.search(r"pull_request|head|merge", ref), (
                        f"Le job `{ident}` de {fichier} se déclenche sur "
                        f"pull_request_target, avec un jeton en écriture, et récupère le "
                        f"code proposé ({ref}). Ce code s'exécute alors avec les droits "
                        "du dépôt. Les tests d'une contribution tournent sur pull_request."
                    )
                commande = str(pas.get("run", ""))
                assert not re.search(r"\b(uv|pip|pytest|npm|make|python)\b", commande), (
                    f"Le job `{ident}` de {fichier} exécute `{commande.strip()[:60]}` "
                    "dans un déclencheur privilégié."
                )


def test_l_equipe_securite_relit_les_chemins_sensibles(projet: Path) -> None:
    codeowners = _codeowners(projet)
    assert codeowners is not None, (
        "Aucun fichier CODEOWNERS (.github/CODEOWNERS, CODEOWNERS ou docs/CODEOWNERS) : "
        "rien n'impose une revue de l'équipe sécurité sur les workflows."
    )
    for chemin in CHEMINS_SENSIBLES:
        proprietaires = _proprietaires(codeowners, chemin)
        assert EQUIPE_SECURITE in proprietaires, (
            f"Une modification de {chemin} revient à {proprietaires or 'personne'} : "
            f"{EQUIPE_SECURITE} doit la relire. Dans CODEOWNERS, la dernière ligne qui "
            "correspond l'emporte."
        )
    proprietaires_app = _proprietaires(codeowners, "src/notes_api/app.py")
    assert proprietaires_app, "Le code de l'application n'a aucun propriétaire dans CODEOWNERS."
    modele = yaml.safe_load((projet / "threat-model.yml").read_text(encoding="utf-8"))
    visees = [m for m in modele.get("threats", []) if str(m.get("id")) == "T-13"]
    assert visees and visees[0].get("status") == "mitigated", (
        "La menace T-13 sur les workflows de pull request passe à `mitigated`."
    )
    assert (projet / str(visees[0].get("evidence") or "")).is_file(), (
        "La preuve de T-13 doit être un fichier du projet : CODEOWNERS ou le pipeline."
    )
