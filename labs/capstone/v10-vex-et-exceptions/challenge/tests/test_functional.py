"""V10, VEX et exceptions datées : cinq contrôles, vingt points chacun.

## Ce que ces tests font

Ils jouent votre pipeline avec act sur une pull request, au seuil MEDIUM que
l'équipe vient d'adopter, puis sur une COPIE dont toutes les exceptions ont
expiré : le pipeline doit redevenir rouge.

Ils construisent aussi deux images : la vôtre, qui ne doit plus contenir pip,
et celle de la version précédente (les fixtures de ce lab), qui le contient
encore. La seconde est analysée par Trivy avec VOTRE document VEX : les
vulnérabilités de pip doivent y être déclarées sans effet sur notes-api, et
rien d'autre ne doit être masqué.

## Pourquoi les identifiants de pip ne sont pas écrits ici

Ils sont lus à l'exécution, dans le rapport de Trivy sur l'image précédente.
Une vulnérabilité publiée demain sur pip 25.0.1 entrerait dans la liste, et
votre VEX devrait la couvrir aussi : c'est exactement ce que vivent ceux qui
exploitent une version déjà livrée.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import secrets
from pathlib import Path

import pytest
import yaml

from conftest import (
    copie_temporaire,
    executer,
    exiger_application,
    exiger_outil,
    exiger_workdir,
    exiger_workflows,
    jouer_act,
    message,
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)
LAB_ID = "capstone-v10-vex-et-exceptions"
FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
TRIVY = "ghcr.io/aquasecurity/trivy:0.75.0@sha256:af6acf9a6b85dfe389a1941505c0ce9efef52a4719635e1a962f022a3d855daa"
VEX = Path("security") / "notes-api.openvex.json"
EXCEPTIONS = Path(".trivyignore.yaml")
JUSTIFICATIONS = {
    "component_not_present",
    "vulnerable_code_not_present",
    "vulnerable_code_not_in_execute_path",
    "vulnerable_code_cannot_be_controlled_by_adversary",
    "inline_mitigations_already_exist",
}
DUREE_MAX = dt.timedelta(days=183)


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


def _construire(contexte: Path, etiquette: str) -> None:
    res = executer(["docker", "build", "-q", "-t", etiquette, "."], cwd=contexte, timeout=900)
    if res.returncode != 0:
        pytest.fail(message(
            en=f"The image of {contexte} does not build:\n" + (res.stdout + res.stderr)[-1200:],
            fr=f"L'image de {contexte} ne se construit pas :\n" + (res.stdout + res.stderr)[-1200:],
        ))


@pytest.fixture(scope="module")
def images(projet: Path, tmp_path_factory):
    exiger_outil("docker")
    suffixe = secrets.token_hex(4)
    nouvelle, ancienne = f"notes-api-controle:v10-{suffixe}", f"notes-api-precedente:v10-{suffixe}"
    _construire(projet, nouvelle)
    _construire(FIXTURES, ancienne)
    dossier = tmp_path_factory.mktemp("archives")
    dossier.chmod(0o755)
    executer(["docker", "save", ancienne, "-o", str(dossier / "precedente.tar")], timeout=300)
    (dossier / "precedente.tar").chmod(0o644)
    yield nouvelle, dossier
    executer(["docker", "rmi", "-f", nouvelle, ancienne], timeout=120)


def _scanner_precedente(dossier: Path, vex: Path | None) -> dict:
    montages = ["-v", f"{dossier}:/w:ro"]
    options = ["--severity", "MEDIUM,HIGH,CRITICAL", "--ignore-unfixed", "--format", "json", "--quiet"]
    if vex is not None:
        montages += ["-v", f"{vex.parent}:/vex:ro"]
        options += ["--vex", f"/vex/{vex.name}", "--show-suppressed"]
    res = executer(
        ["docker", "run", "--rm", *montages, TRIVY, "image", "--input", "/w/precedente.tar", *options],
        timeout=900,
    )
    if res.returncode != 0:
        pytest.fail(message(
            en="Trivy could not analyse the previous image:\n" + res.stderr[-1200:],
            fr="Trivy n'a pas pu analyser l'image précédente :\n" + res.stderr[-1200:],
        ))
    return json.loads(res.stdout)


def _constats(rapport: dict) -> list[dict]:
    return [v for r in rapport.get("Results", []) for v in (r.get("Vulnerabilities") or [])]


def _masques(rapport: dict) -> list[dict]:
    return [m for r in rapport.get("Results", []) for m in (r.get("ExperimentalModifiedFindings") or [])]


def test_le_pipeline_passe_au_seuil_medium(projet: Path) -> None:
    res = jouer_act(projet, "pull_request")
    assert _vert(res), message(
        en="On a pull request, the pipeline must be green.\n  " + res.resume(),
        fr="Sur une pull request, le pipeline doit être vert.\n  " + res.resume(),
    )
    workflows = "\n".join(f.read_text(encoding="utf-8") for f in (projet / ".github" / "workflows").glob("*.y*ml"))
    for portee in ("config", "image"):
        lignes = [x for x in workflows.splitlines() if re.search(rf"args:\s*{portee}\b", x) and "--exit-code" in x]
        assert lignes and all("MEDIUM" in x for x in lignes), message(
            en=f"Trivy's `{portee}` analysis does not block at the MEDIUM threshold yet: "
            "--severity MEDIUM,HIGH,CRITICAL.",
            fr=f"L'analyse `{portee}` de Trivy ne bloque pas encore au seuil MEDIUM : "
            "--severity MEDIUM,HIGH,CRITICAL.",
        )


def test_l_image_ne_contient_plus_pip(projet: Path, images) -> None:
    nouvelle, _ = images
    res = executer(
        ["docker", "run", "--rm", "--network", "none", "--entrypoint", "python", nouvelle, "-c",
         "import importlib.util, shutil; print(importlib.util.find_spec('pip') is None and shutil.which('pip') is None)"],
        timeout=120,
    )
    assert res.stdout.strip().splitlines()[-1:] == ["True"], message(
        en="The image still embeds pip: notes-api never runs it, and a tool that is "
        "absent carries no vulnerability. Remove it from the final image.\n  " + (res.stdout + res.stderr)[-300:],
        fr="L'image embarque encore pip : notes-api ne l'exécute jamais, et un outil absent ne "
        "porte aucune vulnérabilité. Retirez-le de l'image finale.\n  " + (res.stdout + res.stderr)[-300:],
    )


def test_le_vex_couvre_pip_dans_la_version_precedente(projet: Path, images) -> None:
    _, dossier = images
    vex = projet / VEX
    assert vex.is_file(), message(
        en=f"{VEX} cannot be found: nothing tells the operators what was analysed.",
        fr=f"{VEX} est introuvable : rien ne dit aux exploitants ce qui a été analysé.",
    )
    sans = {(v["VulnerabilityID"], v["PkgName"]) for v in _constats(_scanner_precedente(dossier, None))}
    pip = {cve for cve, paquet in sans if paquet == "pip"}
    assert pip, message(
        en="The previous image carries no pip vulnerability: the bench cannot measure any more.",
        fr="L'image précédente ne porte aucune vulnérabilité de pip : le banc ne sait plus mesurer.",
    )
    avec = _scanner_precedente(dossier, vex)
    restants = {(v["VulnerabilityID"], v["PkgName"]) for v in _constats(avec)}
    oublies = sorted(cve for cve, paquet in restants if paquet == "pip")
    assert not oublies, message(
        en=f"With your VEX, Trivy still reports pip for {', '.join(oublies)} in the previous "
        "version: every pip vulnerability must have its statement.",
        fr=f"Avec votre VEX, Trivy signale encore pip pour {', '.join(oublies)} dans la version "
        "précédente : chaque vulnérabilité de pip doit avoir sa déclaration.",
    )
    masques = {(m.get("Finding", {}).get("VulnerabilityID"), m.get("Finding", {}).get("PkgName")) for m in _masques(avec)}
    hors_pip = sorted(f"{cve} ({paquet})" for cve, paquet in masques if paquet != "pip")
    assert not hors_pip, message(
        en=f"Your VEX also masks {', '.join(hors_pip)}: it must declare only what was "
        "analysed, pip, never other packages out of convenience.",
        fr=f"Votre VEX masque aussi {', '.join(hors_pip)} : il ne doit déclarer que ce qui a été "
        "analysé, pip, jamais d'autres paquets par commodité.",
    )


def test_une_exception_expiree_rallume_l_alerte(projet: Path) -> None:
    hier = (dt.datetime.now(tz=dt.UTC).date() - dt.timedelta(days=1)).isoformat()
    with copie_temporaire(projet) as copie:
        fichier = copie / EXCEPTIONS
        assert fichier.is_file(), message(
            en=f"{EXCEPTIONS} cannot be found: no exception is written down.",
            fr=f"{EXCEPTIONS} est introuvable : aucune exception n'est écrite.",
        )
        texte, n = re.subn(r"(?m)^(\s*expired_at:\s*)\S+", rf"\g<1>{hier}", fichier.read_text(encoding="utf-8"))
        assert n, message(
            en=f"{EXCEPTIONS} carries no expiry date (expired_at).",
            fr=f"{EXCEPTIONS} ne porte aucune date d'expiration (expired_at).",
        )
        fichier.write_text(texte, encoding="utf-8")
        res = jouer_act(copie, "pull_request")
    assert _rouge(res), message(
        en=f"A copy whose exceptions have expired ({hier}) must turn the pipeline red: at "
        "the deadline, the decision is revisited.\n  " + res.resume(),
        fr=f"Une copie dont les exceptions ont expiré ({hier}) doit rendre le pipeline rouge : à "
        "l'échéance, la décision se reprend.\n  " + res.resume(),
    )
    assert any(re.search(r"(AWS|KSV)-\d{4}", ligne) for ligne in res.lignes), message(
        en="The pipeline fails, but not on the configuration analysis.\n  " + res.resume(),
        fr="Le pipeline échoue, mais pas sur l'analyse de configuration.\n  " + res.resume(),
    )


def test_chaque_decision_est_ecrite_datee_et_le_modele_a_jour(projet: Path) -> None:
    donnees = yaml.safe_load((projet / EXCEPTIONS).read_text(encoding="utf-8")) or {}
    entrees = [e for cle in ("misconfigurations", "vulnerabilities", "secrets") for e in donnees.get(cle) or []]
    assert entrees, message(
        en=f"{EXCEPTIONS} carries no exception.",
        fr=f"{EXCEPTIONS} ne porte aucune exception.",
    )
    aujourd_hui = dt.datetime.now(tz=dt.UTC).date()
    for entree in entrees:
        ident = entree.get("id", "?")
        assert len(str(entree.get("statement") or "")) >= 60, message(
            en=f"Exception {ident} has no written reason (statement): in six months, nobody "
            "will know why it exists.",
            fr=f"L'exception {ident} n'a pas de raison écrite (statement) : dans six mois, personne "
            "ne saura pourquoi elle existe.",
        )
        echeance = entree.get("expired_at")
        echeance = echeance.date() if isinstance(echeance, dt.datetime) else echeance
        assert isinstance(echeance, dt.date) and aujourd_hui < echeance <= aujourd_hui + DUREE_MAX, message(
            en=f"Exception {ident} must expire within the next six months (expired_at: {echeance}).",
            fr=f"L'exception {ident} doit expirer dans les six prochains mois (expired_at : {echeance}).",
        )
        assert entree.get("paths"), message(
            en=f"Exception {ident} applies to the whole repository: narrow it with paths.",
            fr=f"L'exception {ident} vaut pour tout le dépôt : limitez-la avec paths.",
        )
        assert "infra/deploy.tf" not in (entree.get("paths") or []), message(
            en="The release bucket has no excuse: its versioning gets fixed, not accepted.",
            fr="Le bucket des versions n'a pas d'excuse : son versioning se corrige, il ne s'accepte pas.",
        )
    vex = json.loads((projet / VEX).read_text(encoding="utf-8"))
    for declaration in vex.get("statements", []):
        if declaration.get("status") == "not_affected":
            assert declaration.get("justification") in JUSTIFICATIONS or declaration.get("impact_statement"), message(
                en="A not_affected statement in the VEX has neither a normalised justification "
        "nor an explanation.",
                fr="Une déclaration not_affected du VEX n'a ni justification normalisée ni explication.",
            )
    modele = yaml.safe_load((projet / "threat-model.yml").read_text(encoding="utf-8"))
    visees = [m for m in modele.get("threats", []) if str(m.get("id")) == "T-17"]
    assert visees and visees[0].get("status") == "mitigated", message(
        en="The T-17 threat moves to `mitigated`.",
        fr="La menace T-17 passe à `mitigated`.",
    )
    assert (projet / str(visees[0].get("evidence") or "")).is_file(), message(
        en="The evidence for T-17 must exist.",
        fr="La preuve de T-17 doit exister.",
    )
