"""V7, SBOM et provenance : cinq contrôles, vingt points chacun.

## Ce que ces tests lisent

Comme en V4, act ne fournit pas de jeton OIDC : il ne peut ni signer une
attestation par Sigstore, ni publier quoi que ce soit. Les contrôles se
répartissent donc ainsi :

- act joue le pipeline sur une pull request : l'image est construite, son
  SBOM produit et confronté à uv.lock par l'outil de l'équipe. Une COPIE dont
  l'image installe un paquet hors du verrou doit rendre le pipeline rouge ;
- le job de déploiement est relu : il atteste la provenance de l'archive
  qu'il publie, et publie le SBOM à côté ;
- le script de vérification est EXÉCUTÉ avec un faux `gh` qui enregistre ses
  arguments : il doit exiger le dépôt, le workflow et la référence, et
  propager l'échec de la vérification.
"""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path

import pytest
import yaml

from conftest import (
    copie_temporaire,
    executer,
    exiger_application,
    exiger_workdir,
    exiger_workflows,
    jouer_act,
    lire_workflows,
    references_uses,
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)
LAB_ID = "capstone-v07-sbom-et-provenance"
ATTEST = "actions/attest-build-provenance"
SCRIPT = Path("scripts") / "verify_release.sh"
EXIGENCES = {
    "--repo": "acme/notes-api",
    "--signer-workflow": "acme/notes-api/.github/workflows/ci.yml",
    "--source-ref": "refs/heads/main",
}
FAUX_GH = """\
#!/usr/bin/env bash
printf '%s\\n' "$@" > "$GH_ARGS"
exit "${GH_CODE:-0}"
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


def _job_qui_atteste(projet: Path) -> tuple[str, str, dict]:
    for fichier, workflow in lire_workflows(projet).items():
        for ident, job in (workflow.get("jobs") or {}).items():
            for pas in job.get("steps") or []:
                if isinstance(pas, dict) and str(pas.get("uses", "")).startswith(ATTEST):
                    return fichier, ident, job
    pytest.fail(
        f"Aucun job n'atteste la provenance de ce qu'il publie : l'étape {ATTEST} "
        "manque. Sans elle, une archive remplacée dans le bucket se déploie comme une autre."
    )


def _jouer_verification(projet: Path, tmp_path: Path, code_gh: int) -> tuple[int, list[str]]:
    script = projet / SCRIPT
    assert script.is_file(), f"{SCRIPT} est introuvable : rien ne vérifie une archive avant de la déployer."
    faux = tmp_path / "bin" / "gh"
    faux.parent.mkdir(exist_ok=True)
    faux.write_text(FAUX_GH, encoding="utf-8")
    faux.chmod(faux.stat().st_mode | stat.S_IXUSR)
    archive = tmp_path / "notes-api-0123abc.tgz"
    archive.write_bytes(b"archive de test")
    journal = tmp_path / "gh-args.txt"
    journal.unlink(missing_ok=True)
    res = executer(
        ["bash", str(script), str(archive)],
        cwd=projet,
        env={
            "PATH": f"{faux.parent}{os.pathsep}{os.environ.get('PATH', '')}",
            "GH_ARGS": str(journal),
            "GH_CODE": str(code_gh),
        },
        timeout=60,
    )
    arguments = journal.read_text(encoding="utf-8").splitlines() if journal.is_file() else []
    return res.returncode, arguments


def _valeur(arguments: list[str], option: str) -> str | None:
    for i, argument in enumerate(arguments):
        if argument == option and i + 1 < len(arguments):
            return arguments[i + 1]
        if argument.startswith(option + "="):
            return argument.split("=", 1)[1]
    return None


def test_le_sbom_de_l_image_est_confronte_au_verrou(projet: Path) -> None:
    res = jouer_act(projet, "pull_request")
    assert _vert(res), "Sur une pull request, le pipeline doit être vert.\n  " + res.resume()
    assert any("SBOM matches uv.lock" in ligne for ligne in res.lignes), (
        "Le pipeline ne confronte pas le SBOM de l'image à uv.lock : aucune ligne "
        "« SBOM matches uv.lock » de scripts/check_sbom.py.\n  " + res.resume()
    )


def test_un_paquet_hors_du_verrou_arrete_le_pipeline(projet: Path) -> None:
    with copie_temporaire(projet) as copie:
        dockerfile = copie / "Dockerfile"
        lignes = dockerfile.read_text(encoding="utf-8").splitlines()
        positions = [i for i, ligne in enumerate(lignes) if "uv sync" in ligne]
        assert positions, "Le Dockerfile n'installe plus les dépendances avec uv sync."
        lignes.insert(positions[0] + 1, "RUN uv pip install six==1.17.0")
        dockerfile.write_text("\n".join(lignes) + "\n", encoding="utf-8")
        res = jouer_act(copie, "pull_request")
    assert _rouge(res), (
        "Une copie dont l'image installe six hors de uv.lock doit rendre le pipeline "
        "rouge : un paquet que personne n'a verrouillé ni relu part en production.\n  "
        + res.resume()
    )
    assert any("not in uv.lock" in ligne for ligne in res.lignes), (
        "Le pipeline échoue, mais pas sur la confrontation du SBOM au verrou.\n  " + res.resume()
    )


def test_le_deploiement_atteste_la_provenance_de_l_archive(projet: Path) -> None:
    fichier, ident, job = _job_qui_atteste(projet)
    permissions = job.get("permissions") or {}
    for portee in ("id-token", "attestations"):
        assert permissions.get(portee) == "write", (
            f"Le job `{ident}` de {fichier} doit déclarer `{portee}: write` : Sigstore "
            "signe l'attestation avec le jeton OIDC, et GitHub la range avec ce droit."
        )
    assert "attestations" not in (lire_workflows(projet)[fichier].get("permissions") or {}), (
        f"{fichier} accorde `attestations` au niveau du workflow : ce droit se déclare "
        "sur le seul job qui publie."
    )
    pas = next(p for p in job["steps"] if str(p.get("uses", "")).startswith(ATTEST))
    sujet = str((pas.get("with") or {}).get("subject-path", ""))
    assert sujet.endswith(".tgz"), (
        f"L'attestation porte sur « {sujet or 'rien'} » : elle doit viser l'archive "
        "publiée, celle que l'on vérifiera avant de la déployer."
    )
    refs = [r for r in references_uses(projet) if r.action == ATTEST]
    assert refs and all(r.epinglee_par_sha for r in refs), (
        f"{ATTEST} reçoit le jeton OIDC : il s'épingle par SHA de commit."
    )
    if job.get("if"):
        assert "refs/heads/main" in str(job["if"]), (
            f"Le job `{ident}` doit rester réservé à main : seule main publie et atteste."
        )


def test_la_verification_exige_le_depot_le_workflow_et_main(projet: Path, tmp_path: Path) -> None:
    code, arguments = _jouer_verification(projet, tmp_path, code_gh=0)
    assert code == 0, f"{SCRIPT} échoue alors que la vérification réussit (code {code})."
    assert arguments[:2] == ["attestation", "verify"], (
        f"{SCRIPT} doit appeler `gh attestation verify` ; il a appelé : gh {' '.join(arguments)}"
    )
    assert any(a.endswith("notes-api-0123abc.tgz") for a in arguments), (
        f"{SCRIPT} ne vérifie pas l'archive qu'on lui passe en argument."
    )
    for option, attendu in EXIGENCES.items():
        assert _valeur(arguments, option) == attendu, (
            f"La vérification doit imposer {option} {attendu} ; reçu : "
            f"{_valeur(arguments, option)}. Sans elle, une attestation émise par un autre "
            "dépôt, un autre workflow ou une branche suffirait."
        )
    assert "--deny-self-hosted-runners" in arguments, (
        "La vérification doit refuser une attestation produite sur un runner auto-hébergé."
    )
    code, _ = _jouer_verification(projet, tmp_path, code_gh=1)
    assert code != 0, (
        f"Quand `gh attestation verify` échoue, {SCRIPT} doit échouer aussi : sinon une "
        "archive non attestée se déploierait quand même."
    )


def test_le_sbom_est_publie_et_le_modele_a_jour(projet: Path) -> None:
    _fichier, ident, job = _job_qui_atteste(projet)
    texte = yaml.safe_dump(job)
    assert re.search(r"\.cdx\.json", texte), (
        f"Le job `{ident}` ne publie pas le SBOM (sbom.cdx.json) à côté de l'archive : "
        "celui qui déploie doit pouvoir savoir ce qu'elle contient."
    )
    modele = yaml.safe_load((projet / "threat-model.yml").read_text(encoding="utf-8"))
    visees = [m for m in modele.get("threats", []) if str(m.get("id")) == "T-14"]
    assert visees and visees[0].get("status") == "mitigated", (
        "La menace T-14 sur l'archive publiée passe à `mitigated`."
    )
    assert (projet / str(visees[0].get("evidence") or "")).is_file(), (
        "La preuve de T-14 doit être un fichier du projet : le script de vérification."
    )
