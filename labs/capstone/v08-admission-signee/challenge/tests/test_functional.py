"""V8, l'admission : cinq contrôles, vingt points chacun.

## Ce que ces tests font

Ils montent un cluster kind Kubernetes 1.37, le registre interne
`registry.notes.internal:5000` et Kyverno 1.19.1, puis y appliquent les
politiques de `deploy/policies/`. Ils poussent trois images distinctes : une
signée par la clé de la plateforme, une non signée, une signée par une autre
clé. Ils demandent ensuite l'admission de Pods en `--dry-run=server` : Kyverno
juge chaque demande, rien n'est créé.

## La clé de la plateforme

La clé privée qui correspond à `deploy/signing/cosign.pub` vit dans le KMS de
la plateforme, et les tests ne l'ont pas. Ils génèrent donc une paire
éphémère, et remplacent dans vos politiques le bloc PEM de cette clé publique
par le leur, à l'identique, avant de les appliquer. Une politique qui ne
contient pas la clé de `deploy/signing/cosign.pub` n'est pas remplacée : elle
ne peut alors admettre aucune image de la plateforme.

Comptez trois à quatre minutes : le cluster, le registre et Kyverno se montent
et se détruisent à chaque passage.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from conftest import (
    IMAGE_BASE_BANC,
    banc_kind_kyverno,
    exiger_workdir,
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)
LAB_ID = "capstone-v08-admission-signee"
CLE_PLATEFORME = Path("deploy") / "signing" / "cosign.pub"
POLITIQUES = Path("deploy") / "policies"
TYPES_ACTUELS = {"ValidatingPolicy", "ImageValidatingPolicy"}


def _corps_pem(texte: str) -> str:
    return "".join(
        ligne.strip() for ligne in texte.splitlines() if ligne.strip() and not ligne.strip().startswith("-----")
    )


def _remplacer_cle(manifeste: str, cle_projet: str, cle_test: str) -> tuple[str, bool]:
    """Remplace le bloc PEM de la clé du projet par la clé de test, indentation comprise."""
    lignes = manifeste.splitlines()
    corps_projet = _corps_pem(cle_projet)
    sortie, i, remplace = [], 0, False
    while i < len(lignes):
        ligne = lignes[i]
        if ligne.strip() == "-----BEGIN PUBLIC KEY-----":
            j = i
            while j < len(lignes) and lignes[j].strip() != "-----END PUBLIC KEY-----":
                j += 1
            bloc = "\n".join(lignes[i : j + 1])
            if _corps_pem(bloc) == corps_projet:
                retrait = ligne[: len(ligne) - len(ligne.lstrip())]
                sortie.extend(retrait + x for x in cle_test.strip().splitlines())
                remplace = True
                i = j + 1
                continue
        sortie.append(ligne)
        i += 1
    return "\n".join(sortie) + "\n", remplace


def _documents(projet: Path) -> list[tuple[Path, dict]]:
    docs = []
    for fichier in sorted((projet / POLITIQUES).glob("*.y*ml")):
        for doc in yaml.safe_load_all(fichier.read_text(encoding="utf-8")):
            if isinstance(doc, dict):
                docs.append((fichier, doc))
    return docs


@pytest.fixture(scope="module")
def projet() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    if not (WORKDIR / POLITIQUES).is_dir() or not list((WORKDIR / POLITIQUES).glob("*.y*ml")):
        pytest.fail(f"Aucune politique dans {POLITIQUES}/ : rien ne filtre ce que le cluster admet.")
    return WORKDIR


@pytest.fixture(scope="module")
def cluster(projet: Path):
    cle_projet = (projet / CLE_PLATEFORME).read_text(encoding="utf-8")
    with banc_kind_kyverno("v08") as banc:
        _, cle_test = banc.cle("plateforme")
        images = {
            "signee": banc.pousser_image("notes-api", "signee", signer_avec="plateforme"),
            "nonsignee": banc.pousser_image("notes-api", "nonsignee"),
            "autrecle": banc.pousser_image("notes-api", "autrecle", signer_avec="intrus"),
        }
        banc.appliquer("apiVersion: v1\nkind: Namespace\nmetadata:\n  name: notes-api\n")
        for fichier in sorted((projet / POLITIQUES).glob("*.y*ml")):
            manifeste, _ = _remplacer_cle(fichier.read_text(encoding="utf-8"), cle_projet, cle_test)
            banc.appliquer(manifeste)
        banc.attendre_politiques()
        yield banc, images


def test_une_image_signee_par_la_plateforme_est_admise(cluster) -> None:
    banc, images = cluster
    admis, message = banc.admettre("notes-api", "signee", images["signee"])
    assert admis, (
        "Une image du registre interne signée par la clé de la plateforme doit être admise "
        "dans notes-api. Vos politiques la refusent, ou ne contiennent pas la clé de "
        f"{CLE_PLATEFORME} :\n  {message[-500:]}"
    )


def test_une_image_non_signee_est_refusee(cluster) -> None:
    banc, images = cluster
    admis, _ = banc.admettre("notes-api", "nonsignee", images["nonsignee"])
    assert not admis, (
        "Une image du registre interne SANS signature est admise dans notes-api : rien "
        "n'empêche une image poussée hors du pipeline de tourner."
    )
    res = banc.kubectl(
        "-n", "notes-api", "create", "deployment", "nonsignee", f"--image={images['nonsignee']}",
        "--dry-run=server", "-o", "name", timeout=60,
    )
    assert res.returncode != 0, (
        "Un Deployment dont l'image n'est pas signée est accepté : il serait créé, puis son "
        "ReplicaSet échouerait en silence à chaque Pod. Le refus doit venir dès le Deployment."
    )


def test_une_image_signee_par_une_autre_cle_est_refusee(cluster) -> None:
    banc, images = cluster
    admis, _ = banc.admettre("notes-api", "autrecle", images["autrecle"])
    assert not admis, (
        "Une image signée par une AUTRE clé que celle de la plateforme est admise : la "
        "politique vérifie qu'une signature existe, pas qui l'a posée."
    )


def test_une_image_d_un_autre_registre_est_refusee_dans_notes_api(cluster) -> None:
    banc, _ = cluster
    admis, _ = banc.admettre("notes-api", "dockerhub", IMAGE_BASE_BANC)
    assert not admis, (
        f"L'image {IMAGE_BASE_BANC.split('@')[0]} de Docker Hub est admise dans notes-api : "
        "la vérification de signature ne regarde que le registre interne, il faut aussi "
        "refuser tout autre registre."
    )
    admis, message = banc.admettre("default", "dockerhub", IMAGE_BASE_BANC)
    assert admis, (
        "La même image est refusée dans l'espace de noms default : vos politiques débordent "
        f"de notes-api et bloqueraient le reste du cluster.\n  {message[-400:]}"
    )


def test_les_politiques_sont_bloquantes_et_le_modele_a_jour(projet: Path) -> None:
    docs = _documents(projet)
    cle_projet = (projet / CLE_PLATEFORME).read_text(encoding="utf-8")
    types = {doc.get("kind") for _, doc in docs}
    assert "ClusterPolicy" not in types and "Policy" not in types, (
        "Les politiques kyverno.io/v1 (ClusterPolicy, Policy) sont dépréciées depuis Kyverno "
        "1.17 et leur suppression est annoncée : écrivez des ValidatingPolicy et "
        "ImageValidatingPolicy (policies.kyverno.io/v1)."
    )
    assert "ImageValidatingPolicy" in types, "Aucune ImageValidatingPolicy ne vérifie les signatures."
    for fichier, doc in docs:
        if doc.get("kind") not in TYPES_ACTUELS:
            continue
        spec = doc.get("spec") or {}
        nom = (doc.get("metadata") or {}).get("name")
        assert "Deny" in (spec.get("validationActions") or []), (
            f"{fichier.name} : la politique {nom} ne refuse rien (validationActions sans Deny) : "
            "elle se contente de rapporter."
        )
        assert spec.get("failurePolicy", "Fail") != "Ignore", (
            f"{fichier.name} : failurePolicy Ignore admet tout quand Kyverno ne répond pas."
        )
    texte = "\n".join(f.read_text(encoding="utf-8") for f in sorted((projet / POLITIQUES).glob("*.y*ml")))
    _, contient = _remplacer_cle(texte, cle_projet, cle_projet)
    assert contient, f"Aucune politique ne contient la clé publique de la plateforme ({CLE_PLATEFORME})."
    modele = yaml.safe_load((projet / "threat-model.yml").read_text(encoding="utf-8"))
    visees = [m for m in modele.get("threats", []) if str(m.get("id")) == "T-15"]
    assert visees and visees[0].get("status") == "mitigated", (
        "La menace T-15 sur l'admission passe à `mitigated`."
    )
    assert (projet / str(visees[0].get("evidence") or "")).is_file(), (
        "La preuve de T-15 doit être un fichier du projet : une politique d'admission."
    )
