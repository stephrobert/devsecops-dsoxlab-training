"""Méta-tests du dépôt : une pratique SSDF citée existe, et garde son sens.

## Le défaut que ces tests ferment

Chaque version du fil rouge met en oeuvre une ou plusieurs pratiques du NIST
SSDF, et son scénario le dit : « Pratique SSDF visée : PS.1 (protéger le code
contre l'accès non autorisé et l'altération) ». Un code de pratique se trompe
sans bruit : PW.7 (relire le code source) et PW.8 (tester l'exécutable) se
ressemblent, et PW.3, qui existait en version 1.0, n'existe plus en 1.1. Un
code faux reste un code valide, et aucun test d'exécution ne l'attrape.

Le modèle est le test du catalogue Terraform, qui a fermé le même défaut sur
deux grilles d'examen qui se ressemblaient.

## Deux contrôles, et pourquoi le premier ne suffit pas

Le premier vérifie que le code **existe** dans la grille. Il laisserait passer
un PW.7 cité pour un lab qui fait tester un exécutable. Le second compare donc
le **libellé** que le lab accole à son code aux fragments que
`curriculums.yml` associe à ce code. Il refuse une contradiction ; il ne note
pas la rédaction.
"""

import re
import unicodedata
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
LABS = REPO / "labs"
SOURCE = REPO / "curriculums.yml"

FICHIERS_LUS = ("scenario.fr.md", "scenario.md")

# « Pratique SSDF visée : PS.1 (libellé) » et « SSDF practice targeted: PS.1
# (label) ». Plusieurs pratiques se citent l'une après l'autre, chacune avec son
# libellé entre parenthèses.
CITATION = re.compile(
    r"(?:[Pp]ratiques? SSDF visées?|SSDF practices? targeted)\s*:\s*(?P<suite>[^\n]+)"
)
CODE_LIBELLE = re.compile(r"\*{0,2}(?P<code>(?:PO|PS|PW|RV)\.\d)\*{0,2}(?:\s*\((?P<libelle>[^)]{1,160})\))?")


def grille() -> dict:
    return yaml.safe_load(SOURCE.read_text(encoding="utf-8"))["curriculums"]["ssdf"]


def mots_cles() -> dict:
    return yaml.safe_load(SOURCE.read_text(encoding="utf-8"))["mots_cles"]


def tous_les_labs() -> list[str]:
    return sorted(str(c.parent.relative_to(LABS)) for c in LABS.rglob("lab.yaml"))


def citations(rel: str) -> list[tuple[str, str, str]]:
    """(fichier, code, libellé) pour chaque pratique citée par un lab."""
    trouvees = []
    for nom in FICHIERS_LUS:
        chemin = LABS / rel / nom
        if not chemin.is_file():
            continue
        for ligne in CITATION.finditer(chemin.read_text(encoding="utf-8")):
            for m in CODE_LIBELLE.finditer(ligne.group("suite")):
                trouvees.append((nom, m.group("code"), m.group("libelle") or ""))
    return trouvees


def _sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte.lower()) if unicodedata.category(c) != "Mn")


# ---------------------------------------------------------------------------
# 1. L'intégrité de la source elle-même.
# ---------------------------------------------------------------------------


def test_la_grille_porte_sa_provenance() -> None:
    """Une grille sans URL ni date de vérification ne se confronte pas."""
    g = grille()
    assert g["source"].startswith("https://csrc.nist.gov/"), "La grille ne cite pas sa source officielle."
    assert g["pdf"].startswith("https://nvlpubs.nist.gov/"), "La grille ne cite pas le PDF officiel."
    assert g["derniere_verification"], "La grille ne dit pas quand elle a été confrontée au publié."


def test_la_grille_a_les_dix_neuf_pratiques_publiees() -> None:
    """Relevé le 2026-10-03 dans le PDF officiel : 19 pratiques, PW.3 absente."""
    pratiques = grille()["pratiques"]
    assert len(pratiques) == 19, f"La grille déclare {len(pratiques)} pratiques, 19 publiées en version 1.1."
    assert "PW.3" not in pratiques, "PW.3 a été répartie entre PO.1 et PW.4 en version 1.1 : elle n'existe plus."
    groupes = {code.split(".")[0] for code in pratiques}
    assert groupes == set(grille()["groupes"]), f"Groupes de pratiques : {sorted(groupes)}."


def test_chaque_pratique_a_ses_mots_cles() -> None:
    manquants = sorted(set(grille()["pratiques"]) - set(mots_cles()))
    assert not manquants, f"Pratiques sans fragments de libellé : {manquants}."


# ---------------------------------------------------------------------------
# 2. Ce que les labs en citent.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rel", tous_les_labs())
def test_chaque_lab_cite_au_moins_une_pratique(rel: str) -> None:
    """Le fil rouge met en oeuvre le SSDF version après version : chaque lab le dit."""
    for nom in FICHIERS_LUS:
        codes = [c for f, c, _ in citations(rel) if f == nom]
        assert codes, (
            f"{rel}/{nom} ne cite aucune pratique SSDF. Ajoutez une ligne "
            "« Pratique SSDF visée : PO.3 (libellé) » ou « SSDF practice targeted: "
            "PO.3 (label) »."
        )


@pytest.mark.parametrize("rel", tous_les_labs())
def test_une_pratique_citee_existe(rel: str) -> None:
    connues = set(grille()["pratiques"])
    inconnues = sorted({c for _f, c, _l in citations(rel)} - connues)
    assert not inconnues, f"{rel} cite {inconnues}, absente(s) de la grille SSDF 1.1."


@pytest.mark.parametrize("rel", tous_les_labs())
def test_le_libelle_ne_contredit_pas_la_grille(rel: str) -> None:
    for fichier, code, libelle in citations(rel):
        if not libelle:
            continue
        fragments = mots_cles().get(code, [])
        assert any(f in _sans_accents(libelle) for f in fragments), (
            f"{rel}/{fichier} accole « {libelle} » à {code}, qui désigne « "
            f"{grille()['pratiques'][code]['fr']} ». Soit le code vient d'une autre "
            "pratique, soit le libellé juste n'est pas encore couvert par "
            f"`mots_cles.{code}` dans curriculums.yml."
        )
