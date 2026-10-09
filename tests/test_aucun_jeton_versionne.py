"""Méta-tests du dépôt : aucun secret ne doit entrer dans l'historique.

## Pourquoi ce contrôle existe

Le dépôt lance déjà trufflehog, et c'est bien — mais il le lance avec
``--results=verified``, ce qui ne signale **que** les secrets qu'il a pu
valider auprès du service concerné. Par construction, une clé AWS révoquée, un
jeton GitHub expiré, un PAT GitLab factice ou un secret inventé pour un exemple
ne déclenchent **rien**. Ils restent pourtant dans l'historique git d'un dépôt
public, et un lecteur n'a aucun moyen de deviner lequel était vrai.

Ce catalogue a une raison de plus de s'en préoccuper : sa matière première est
du code volontairement vulnérable, et son lab V2 pose délibérément un faux
jeton dans une COPIE du projet pour voir le pipeline se fermer. La frontière
entre « faux jeton pédagogique » et « vrai secret oublié » est exactement ce
qu'un contrôle doit tenir à notre place.

## Ce qu'il lit

Les fichiers que **git porte** (``git ls-files``), et non le répertoire de
travail. C'est le bon périmètre : un fichier ignoré ne peut pas entrer dans
l'historique tant que personne ne l'ajoute, tandis qu'un fichier ajouté avec
``git add -f`` est suivi et sera donc examiné. Le mot de passe du vault et la
clé SSH du formateur, tous deux ignorés et présents sur le disque, sortent ainsi
du balayage sans qu'on ait eu à les nommer.

## Ce qu'il cherche

Des formes qui ne se rencontrent pas par hasard :

- un jeton GitHub classique, ``ghp_`` suivi de 36 caractères ;
- un jeton GitHub à portée fine, ``github_pat_`` suivi de 80 caractères ou plus ;
- un PAT GitLab, ``glpat-`` suivi de 20 caractères ;
- une clé d'accès AWS, ``AKIA`` suivi de 16 majuscules, sauf l'exemple officiel
  d'AWS, que la documentation emploie partout ;
- un en-tête de clé privée au format PEM.

## Ce qu'il ne peut pas faire

Il lit l'état présent, pas l'historique : un jeton committé puis retiré reste
dans les objets git. C'est une raison de plus pour **révoquer** plutôt que pour
retirer.

Il a été éprouvé dans les deux sens : les motifs reconnaissent des valeurs à la
forme exacte d'un vrai secret, construites et jamais écrites — sinon ce fichier
se dénoncerait lui-même, et la seule autre issue serait de l'exclure du
balayage, c'est-à-dire d'ouvrir un trou pour que le contrôle passe.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

# ── Les formes d'un vrai secret ─────────────────────────────────────────────
JETON_GITHUB = re.compile(r"\bghp_[A-Za-z0-9]{36}\b")
JETON_GITHUB_FIN = re.compile(r"\bgithub_pat_[A-Za-z0-9_]{80,}")
JETON_GITLAB = re.compile(r"\bglpat-[A-Za-z0-9_-]{20}\b")

# `AKIAIOSFODNN7EXAMPLE` est l'exemple officiel d'AWS : il figure dans leur
# documentation comme dans celle de HashiCorp, et un lab a le droit de s'en
# servir pour montrer ce qu'il ne faut pas faire.
CLE_AWS = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
EXEMPLES_ADMIS = {"AKIAIOSFODNN7EXAMPLE"}

CLE_PRIVEE = re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")

# Les fichiers de secrets n'ont rien à faire ici, quel que soit leur contenu.
NOMS_INTERDITS = {".vault-pass", ".vault-pass.txt", ".env", "credentials.tfrc.json"}

SUFFIXES_IGNORES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".whl", ".ico"}


def fichiers_suivis() -> list[Path]:
    """Ce que git porte, à l'index comme dans les commits."""
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO, capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        pytest.skip("git ne répond pas : le périmètre du balayage est indéterminé")
    chemins = [REPO / nom for nom in proc.stdout.split("\0") if nom]
    return sorted(
        c for c in chemins
        if c.is_file() and c.suffix not in SUFFIXES_IGNORES
    )


FICHIERS = fichiers_suivis()


def lire(chemin: Path) -> str:
    try:
        return chemin.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


@pytest.mark.parametrize("chemin", FICHIERS, ids=lambda c: str(c.relative_to(REPO)))
def test_aucun_fichier_suivi_ne_porte_de_secret(chemin: Path) -> None:
    rel = chemin.relative_to(REPO)
    contenu = lire(chemin)

    assert chemin.name not in NOMS_INTERDITS, (
        f"{rel} est un fichier de secrets, et il est SUIVI par git.\n\n"
        "Retirez-le de l'index (`git rm --cached`), puis changez le secret "
        "qu'il portait : un fichier retiré reste dans l'historique."
    )

    for motif, quoi, geste in (
        (JETON_GITHUB, "un jeton GitHub", "Révoquez-le sur github.com/settings/tokens"),
        (JETON_GITHUB_FIN, "un jeton GitHub à portée fine", "Révoquez-le sur github.com/settings/tokens"),
        (JETON_GITLAB, "un PAT GitLab", "Révoquez-le dans les réglages d'accès de GitLab"),
    ):
        trouve = motif.search(contenu)
        assert trouve is None, (
            f"{rel} porte ce qui ressemble à {quoi}, à la ligne "
            f"{contenu[: trouve.start()].count(chr(10)) + 1}.\n\n{geste} : le "
            "retirer du fichier ne suffit pas, il reste dans l'historique git."
        )

    cles = set(CLE_AWS.findall(contenu)) - EXEMPLES_ADMIS
    assert not cles, (
        f"{rel} porte une clé d'accès AWS qui n'est pas l'exemple officiel : "
        f"{sorted(cles)}.\n\nSeul `AKIAIOSFODNN7EXAMPLE` est admis, et "
        "uniquement pour montrer ce qu'il ne faut pas faire."
    )

    trouve = CLE_PRIVEE.search(contenu)
    assert trouve is None, (
        f"{rel} porte un en-tête de clé privée, à la ligne "
        f"{contenu[: trouve.start()].count(chr(10)) + 1}.\n\nUne clé privée ne "
        "se versionne jamais : seule la partie publique se partage. Retirez-la "
        "et régénérez la paire."
    )


def test_le_controle_lit_bien_quelque_chose() -> None:
    """Un balayage qui ne trouve plus aucun fichier serait vert et muet."""
    assert len(FICHIERS) >= 200, (
        f"Seuls {len(FICHIERS)} fichiers suivis sont examinés, ce qui est trop "
        "peu pour ce dépôt : `git ls-files` ou les exclusions ont dérivé."
    )


def test_les_motifs_reconnaissent_un_vrai_secret() -> None:
    """Le contrôle doit VOIR ce qu'il prétend voir.

    Sans ce test, une expression régulière cassée rendrait tout le fichier vert,
    et c'est la forme la plus discrète de faux vert : plus rien n'est détecté,
    donc tout passe.

    Les valeurs sont CONSTRUITES, jamais écrites : un secret à la forme exacte
    recopié ici ferait échouer le balayage sur ce fichier même.
    """
    faux_github = "gh" + "p_" + "A" * 36
    assert JETON_GITHUB.search(f'GITHUB_TOKEN = "{faux_github}"'), (
        "Le motif ne reconnaît plus un jeton GitHub."
    )
    assert JETON_GITHUB.search("ghp_trop_court") is None, (
        "Le motif se déclenche sur un préfixe sans la longueur attendue."
    )

    faux_fin = "github" + "_pat_" + "B" * 82
    assert JETON_GITHUB_FIN.search(faux_fin), (
        "Le motif ne reconnaît plus un jeton GitHub à portée fine."
    )

    faux_gitlab = "gl" + "pat-" + "C" * 20
    assert JETON_GITLAB.search(faux_gitlab), "Le motif ne reconnaît plus un PAT GitLab."

    fausse_cle = "AKIA" + "Z" * 16
    assert CLE_AWS.findall(fausse_cle) == [fausse_cle]
    assert not (set(CLE_AWS.findall("AKIA" + "IOSFODNN7EXAMPLE")) - EXEMPLES_ADMIS), (
        "L'exemple officiel doit rester admis, sinon un lab ne peut plus montrer "
        "ce qu'il faut éviter."
    )

    entete = "-----BEGIN" + " OPENSSH PRIVATE KEY" + "-----"
    assert CLE_PRIVEE.search(entete), "Le motif ne reconnaît plus un en-tête de clé privée."
    assert CLE_PRIVEE.search("-----BEGIN PUBLIC KEY-----") is None, (
        "Le motif se déclenche sur une clé PUBLIQUE, que les labs partagent "
        "légitimement — quatre `cosign.pub` en dépendent."
    )


def test_le_perimetre_est_bien_ce_que_git_porte() -> None:
    """Le choix de `git ls-files` est ce qui rend ce test juste, et il se mesure.

    Le mot de passe du vault et la clé SSH du formateur existent sur le disque,
    sont ignorés, et doivent rester HORS du balayage : les signaler serait un
    faux positif permanent, et un contrôle qu'on apprend à ignorer ne contrôle
    plus rien.
    """
    noms = {str(f.relative_to(REPO)) for f in FICHIERS}
    for ignore in (".vault-pass", "ssh/id_ed25519"):
        if (REPO / ignore).exists():
            assert ignore not in noms, (
                f"{ignore} est présent sur le disque ET suivi par git : c'est "
                "exactement ce que ce test refuse."
            )
