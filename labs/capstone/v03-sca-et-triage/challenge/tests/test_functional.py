"""V3, analyse des dépendances et triage : cinq contrôles, vingt points chacun.

## Ce que ces tests lisent

Ce qu'act PRODUIT en jouant le pipeline de l'apprenant : le résultat du job,
et les lignes qu'osv-scanner et pytest écrivent. Pour voir la porte se fermer,
une COPIE du projet retrouve le verrou vulnérable de départ, ou une exception
dont la date est passée : le pipeline doit devenir rouge.

Les deux autres contrôles relisent le projet : les versions verrouillées, et
le fichier de triage `osv-scanner.toml`.

## Pourquoi une exception est permise, et une seule

Sur le verrou de départ, osv-scanner 2.6.0 rapporte huit vulnérabilités
(mesuré le 2026-10-03). Sept ont une version corrigée : elles se corrigent,
elles ne s'excusent pas. La huitième, l'attaque Minerva sur ecdsa
(GHSA-wj6h-64fc-37mp, CVE-2024-23342), n'a pas de correctif et n'en aura pas.
C'est la seule que le triage peut accepter, avec une raison et une date.
"""

from __future__ import annotations

import datetime as dt
import re
import shutil
import tomllib
from pathlib import Path

import pytest
import yaml

from conftest import (
    copie_temporaire,
    exiger_application,
    exiger_workdir,
    exiger_workflows,
    jouer_act,
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)
LAB_ID = "capstone-v03-sca-et-triage"
FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
MINERVA = {"GHSA-wj6h-64fc-37mp", "CVE-2024-23342", "PYSEC-2026-1325"}
# La plus petite version qui corrige toutes les vulnérabilités connues du
# paquet, relevée sur osv.dev le 2026-10-03.
VERSIONS_CORRIGEES = {"flask": (3, 1, 3), "werkzeug": (3, 1, 6), "ecdsa": (0, 19, 2)}
DUREE_MAX = dt.timedelta(days=183)


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


def _version(texte: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", texte)[:3])


def _verrouillees(projet: Path) -> dict[str, str]:
    verrou = tomllib.loads((projet / "uv.lock").read_text(encoding="utf-8"))
    return {p["name"]: p["version"] for p in verrou.get("package", []) if "version" in p}


def _exceptions(projet: Path) -> list[dict]:
    fichier = projet / "osv-scanner.toml"
    if not fichier.is_file():
        return []
    return tomllib.loads(fichier.read_text(encoding="utf-8")).get("IgnoredVulns", [])


def test_le_pipeline_analyse_les_dependances_et_passe(jeu_livre) -> None:
    assert _vert(jeu_livre), "Sur le projet tel quel, le pipeline doit être vert.\n  " + jeu_livre.resume()
    assert any(re.search(r"Scanned .*uv\.lock.* found \d+ packages", ligne) for ligne in jeu_livre.lignes), (
        "Le pipeline ne montre aucune analyse des dépendances : osv-scanner n'a pas "
        "lu uv.lock.\n  " + jeu_livre.resume()
    )
    assert any(re.search(r"\b\d+ passed\b.* in [0-9.]+s", ligne) for ligne in jeu_livre.lignes), (
        "Les tests de l'application ne tournent plus dans le pipeline.\n  " + jeu_livre.resume()
    )


def test_le_verrou_vulnerable_arrete_le_pipeline(projet: Path) -> None:
    assert (FIXTURES / "uv.lock").is_file(), f"Verrou de départ introuvable : {FIXTURES / 'uv.lock'}"
    with copie_temporaire(projet) as copie:
        for nom in ("pyproject.toml", "uv.lock"):
            shutil.copy2(FIXTURES / nom, copie / nom)
        res = jouer_act(copie, "push")
    assert _rouge(res), (
        "Une copie qui retrouve le verrou de départ (flask et werkzeug 3.0.3, ecdsa "
        "0.19.1) doit rendre le pipeline rouge : l'analyse des dépendances doit "
        "BLOQUER, pas seulement signaler.\n  " + res.resume()
    )
    assert any("werkzeug" in ligne and "3.0.3" in ligne for ligne in res.lignes), (
        "Le pipeline échoue, mais pas sur l'analyse des dépendances : aucune ligne "
        "ne cite werkzeug 3.0.3.\n  " + res.resume()
    )


def test_les_vulnerabilites_corrigeables_sont_corrigees(projet: Path) -> None:
    versions = _verrouillees(projet)
    for paquet, minimum in VERSIONS_CORRIGEES.items():
        assert paquet in versions, f"{paquet} a disparu de uv.lock : l'application en a besoin."
        assert _version(versions[paquet]) >= minimum, (
            f"uv.lock verrouille {paquet} {versions[paquet]}, encore vulnérable : la "
            f"version corrigée est {'.'.join(map(str, minimum))}. Une vulnérabilité "
            "qui a un correctif se corrige, elle ne s'excuse pas."
        )
    hors_minerva = [str(e.get("id")) for e in _exceptions(projet) if str(e.get("id")) not in MINERVA]
    assert not hors_minerva, (
        f"osv-scanner.toml accepte {', '.join(hors_minerva)} : seule l'attaque Minerva "
        "(GHSA-wj6h-64fc-37mp) n'a pas de version corrigée. Le reste se met à jour."
    )
    dockerfile = (projet / "Dockerfile").read_text(encoding="utf-8")
    assert not re.search(r"==3\.0\.3|ecdsa==0\.19\.1", dockerfile), (
        "Le Dockerfile installe encore les versions vulnérables : osv-scanner lit "
        "uv.lock, pas cette ligne. Alignez-la sur le verrou."
    )


def test_l_exception_est_justifiee_datee_et_le_modele_a_jour(projet: Path) -> None:
    minerva = [e for e in _exceptions(projet) if str(e.get("id")) in MINERVA]
    assert minerva, (
        "osv-scanner.toml n'accepte pas l'attaque Minerva (GHSA-wj6h-64fc-37mp) : "
        "sans correctif publié, elle se trie, avec une raison et une date."
    )
    exception = minerva[0]
    raison = str(exception.get("reason") or "")
    assert len(raison) >= 80 and re.search(r"verif|verify", raison, re.I), (
        "La raison doit dire pourquoi le risque est acceptable ICI : l'attaque vise "
        "la signature, et notes-api ne fait que vérifier. Une raison qui ne cite "
        f"pas la vérification ne se relit pas contre le code. Lu : « {raison} »"
    )
    echeance = exception.get("ignoreUntil")
    if isinstance(echeance, dt.datetime):
        echeance = echeance.date()
    assert isinstance(echeance, dt.date), (
        "L'exception n'a pas de date d'expiration (ignoreUntil) : une exception sans "
        "échéance est une décision qu'on ne reprend jamais."
    )
    aujourd_hui = dt.datetime.now(tz=dt.UTC).date()
    assert aujourd_hui < echeance <= aujourd_hui + DUREE_MAX, (
        f"ignoreUntil vaut {echeance} : elle doit tomber dans les six prochains mois, "
        "assez loin pour migrer, assez près pour que la décision soit reprise."
    )
    modele = yaml.safe_load((projet / "threat-model.yml").read_text(encoding="utf-8"))
    dependances = [
        m for m in modele.get("threats", [])
        if str(m.get("component", "")).strip().lower() == "dependencies"
    ]
    assert dependances and dependances[0].get("status") == "mitigated", (
        "La menace sur les dépendances (T-08) passe à `mitigated` : le pipeline les "
        "analyse désormais à chaque push."
    )
    assert (projet / str(dependances[0].get("evidence") or "")).is_file(), (
        "La preuve de T-08 doit être un fichier du projet : le triage ou le pipeline."
    )


def test_une_exception_expiree_rallume_l_alerte(projet: Path) -> None:
    hier = (dt.datetime.now(tz=dt.UTC).date() - dt.timedelta(days=1)).isoformat()
    with copie_temporaire(projet) as copie:
        triage = copie / "osv-scanner.toml"
        assert triage.is_file(), "osv-scanner.toml manque : le triage n'est pas versionné."
        texte, n = re.subn(r"(?m)^(\s*ignoreUntil\s*=\s*)\S+", rf"\g<1>{hier}", triage.read_text(encoding="utf-8"))
        assert n, "osv-scanner.toml ne porte aucune ligne ignoreUntil."
        triage.write_text(texte, encoding="utf-8")
        res = jouer_act(copie, "push")
    assert _rouge(res), (
        f"Une copie dont l'exception a expiré (ignoreUntil = {hier}) doit rendre le "
        "pipeline rouge : à l'échéance, la décision se reprend.\n  " + res.resume()
    )
    assert any("GHSA-wj6h-64fc-37mp" in ligne for ligne in res.lignes), (
        "Le pipeline échoue, mais pas sur la vulnérabilité dont l'exception a "
        "expiré.\n  " + res.resume()
    )
