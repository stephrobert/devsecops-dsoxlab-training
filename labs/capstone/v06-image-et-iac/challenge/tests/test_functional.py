"""V6, l'image et l'infrastructure : cinq contrôles, vingt points chacun.

## Ce que ces tests lisent

Ce qu'act PRODUIT en jouant le pipeline sur une pull request : le résultat
des jobs, et les lignes que Trivy écrit en analysant la configuration
(« Detected config files ») et l'image (« Detected OS »). Pour voir les
portes se fermer, une COPIE du projet reçoit un Dockerfile sans USER, ou un
security group qui ouvre SSH au monde : le pipeline doit devenir rouge, sur
la règle attendue.

Le quatrième contrôle construit l'image lui-même et l'interroge : l'utilisateur
qui l'exécute, les versions qu'elle embarque, ce qu'elle n'embarque pas.

## Pourquoi --ignore-unfixed n'est pas une complaisance

Mesuré le 2026-10-03 : l'image python:3.12-slim du jour portait une CVE HIGH
de libpcre2 déjà corrigée dans Debian, mais pas encore dans l'image de base.
Une image figée par digest finit toujours par en porter une. La solution
applique les correctifs Debian à chaque construction ; ce qui n'a pas de
correctif publié ne se corrige pas en reconstruisant, et relève du triage de
V3, pas d'une porte de build.
"""

from __future__ import annotations

import json
import re
import secrets
import tomllib
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
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)
LAB_ID = "capstone-v06-image-et-iac"
SSH_OUVERT = """

resource "aws_security_group" "bastion" {
  name        = "bastion"
  description = "Acces SSH de secours"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
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


@pytest.fixture(scope="module")
def image(projet: Path):
    """L'image du projet, construite pour ce contrôle et supprimée ensuite."""
    exiger_outil("docker")
    etiquette = f"notes-api-controle:{secrets.token_hex(6)}"
    res = executer(["docker", "build", "-q", "-t", etiquette, "."], cwd=projet, timeout=900)
    if res.returncode != 0:
        pytest.fail("L'image du projet ne se construit pas :\n" + (res.stdout + res.stderr)[-1500:])
    yield etiquette
    executer(["docker", "rmi", "-f", etiquette], timeout=120)


def _dans_l_image(etiquette: str, script: str) -> tuple[int, str]:
    res = executer(
        ["docker", "run", "--rm", "--network", "none", "--entrypoint", "python", etiquette, "-c", script],
        timeout=120,
    )
    return res.returncode, (res.stdout + res.stderr).strip()


def test_l_image_et_l_infra_sont_analysees_et_le_projet_passe(projet: Path) -> None:
    res = jouer_act(projet, "pull_request")
    assert _vert(res), "Sur une pull request, le pipeline doit être vert.\n  " + res.resume()
    assert any("Detected config files" in ligne for ligne in res.lignes), (
        "Le pipeline n'analyse pas la configuration : aucune ligne « Detected config "
        "files » de Trivy.\n  " + res.resume()
    )
    assert any("Detected OS" in ligne for ligne in res.lignes), (
        "Le pipeline n'analyse pas l'image construite : aucune ligne « Detected OS » "
        "de Trivy.\n  " + res.resume()
    )


def test_un_dockerfile_sans_utilisateur_arrete_le_pipeline(projet: Path) -> None:
    with copie_temporaire(projet) as copie:
        dockerfile = copie / "Dockerfile"
        texte = dockerfile.read_text(encoding="utf-8")
        sans_user = "\n".join(x for x in texte.splitlines() if not x.strip().upper().startswith("USER "))
        assert sans_user != texte.rstrip("\n"), "Le Dockerfile ne déclare aucun USER."
        dockerfile.write_text(sans_user + "\n", encoding="utf-8")
        res = jouer_act(copie, "pull_request")
    assert _rouge(res), (
        "Une copie dont le Dockerfile n'a plus de USER doit rendre le pipeline rouge : "
        "une image qui tourne en root fait d'une faille de l'application une faille "
        "du conteneur.\n  " + res.resume()
    )
    assert any("DS-0002" in ligne for ligne in res.lignes), (
        "Le pipeline échoue, mais pas sur l'analyse de configuration : Trivy n'a pas "
        "signalé DS-0002.\n  " + res.resume()
    )


def test_un_ssh_ouvert_au_monde_arrete_le_pipeline(projet: Path) -> None:
    with copie_temporaire(projet) as copie:
        main = copie / "infra" / "main.tf"
        main.write_text(main.read_text(encoding="utf-8") + SSH_OUVERT, encoding="utf-8")
        res = jouer_act(copie, "pull_request")
    assert _rouge(res), (
        "Une copie qui ajoute un security group ouvrant SSH à 0.0.0.0/0 doit rendre le "
        "pipeline rouge : l'analyse de l'infrastructure doit BLOQUER.\n  " + res.resume()
    )
    assert any("AWS-0107" in ligne for ligne in res.lignes), (
        "Le pipeline échoue, mais pas sur l'analyse de l'infrastructure : Trivy n'a pas "
        "signalé AWS-0107.\n  " + res.resume()
    )


def test_l_image_tourne_sans_privilege_avec_le_verrou(projet: Path, image: str) -> None:
    dockerfile = (projet / "Dockerfile").read_text(encoding="utf-8")
    for ligne in dockerfile.splitlines():
        if ligne.strip().upper().startswith("FROM ") or "--from=" in ligne:
            reference = re.search(r"(?:FROM\s+|--from=)(\S+)", ligne, re.I).group(1)
            if "/" not in reference and ":" not in reference and "@" not in reference:
                continue  # le nom d'une étape précédente
            assert "@sha256:" in reference, (
                f"Le Dockerfile tire {reference} sans digest : l'image de base changerait "
                "sous vos pieds, d'un build à l'autre."
            )
    inspect = json.loads(executer(["docker", "image", "inspect", image], timeout=60).stdout)[0]
    utilisateur = str(inspect["Config"].get("User") or "")
    assert utilisateur not in ("", "0", "root") and not utilisateur.startswith(("0:", "root:")), (
        f"L'image s'exécute en tant que « {utilisateur or 'root'} » : déclarez un "
        "utilisateur sans privilège avec USER."
    )
    code, sortie = _dans_l_image(image, "import os, notes_api.app; print(os.getuid())")
    assert code == 0 and sortie.splitlines()[-1] != "0", (
        f"Dans l'image, l'application doit s'importer sous un uid non nul. Lu : {sortie[-400:]}"
    )
    verrou = tomllib.loads((projet / "uv.lock").read_text(encoding="utf-8"))
    versions = {p["name"]: p["version"] for p in verrou.get("package", []) if "version" in p}
    script = (
        "import importlib.metadata as m, json\n"
        "noms = ['flask', 'werkzeug', 'cryptography', 'pytest']\n"
        "out = {}\n"
        "for n in noms:\n"
        "    try:\n"
        "        out[n] = m.version(n)\n"
        "    except m.PackageNotFoundError:\n"
        "        out[n] = None\n"
        "print(json.dumps(out))\n"
    )
    code, sortie = _dans_l_image(image, script)
    assert code == 0, f"Impossible d'interroger l'image : {sortie[-400:]}"
    embarque = json.loads(sortie.splitlines()[-1])
    for paquet in ("flask", "werkzeug", "cryptography"):
        assert embarque[paquet] == versions.get(paquet), (
            f"L'image embarque {paquet} {embarque[paquet]}, le verrou dit "
            f"{versions.get(paquet)} : l'image doit s'installer depuis uv.lock, pas "
            "depuis une liste recopiée à la main qui dérive."
        )
    assert embarque["pytest"] is None, (
        "L'image embarque pytest : les dépendances de développement n'ont rien à faire "
        "en production."
    )


def test_le_modele_dit_l_image_et_l_infra_traitees(projet: Path) -> None:
    infra = "\n".join(p.read_text(encoding="utf-8") for p in sorted((projet / "infra").glob("*.tf")))
    for bloc in re.findall(r"ingress\s*\{(.*?)\}", infra, re.S):
        assert "0.0.0.0/0" not in bloc, (
            "Un security group accepte encore du trafic de 0.0.0.0/0 : l'API se joint "
            "depuis le load balancer du VPC, jamais directement depuis Internet."
        )
    modele = yaml.safe_load((projet / "threat-model.yml").read_text(encoding="utf-8"))
    menaces = {str(m.get("id")): m for m in modele.get("threats", [])}
    for ident, sujet in (("T-09", "l'image qui tourne en root"), ("T-10", "le security group ouvert")):
        assert ident in menaces, f"Le modèle ne porte plus la menace {ident}."
        assert menaces[ident].get("status") == "mitigated", (
            f"La menace {ident} ({sujet}) passe à `mitigated`."
        )
        assert (projet / str(menaces[ident].get("evidence") or "")).is_file(), (
            f"La preuve de {ident} doit être un fichier du projet."
        )
