"""V11, mesurer la fiabilité : cinq contrôles, vingt points chacun.

## Ce que ces tests font

- Ils jouent votre pipeline avec act : les règles d'alerte sont vérifiées et
  testées par promtool, et les métriques DORA calculées.
- Ils soumettent VOTRE règle d'alerte à leurs propres séries de requêtes,
  avec promtool : 10 % d'erreurs doivent déclencher NotesApiErrorBudgetBurn,
  1 % ne le doit pas. Le test demande « aucune alerte » et lit ce que promtool
  a réellement vu sous `got:` : vos labels sont libres, seul compte le fait
  que l'alerte sonne ou non.
- Ils exécutent `scripts/dora.py` sur des journaux qu'ils fabriquent, dont ils
  connaissent les bonnes réponses.
- Ils relisent le runbook, et vérifient que l'alerte y renvoie.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import statistics
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
LAB_ID = "capstone-v11-slo-et-dora"
PROMETHEUS = "prom/prometheus:v3.15.0@sha256:efd719c99d83b060d9daefdcf00360461adf279f45ef5391f8d111892118753e"
ALERTES = Path("ops") / "alerts.yaml"
RUNBOOK = Path("ops") / "runbooks" / "notes-api-indisponible.md"
ALERTE = "NotesApiErrorBudgetBurn"
SECTIONS = {
    "symptômes": r"sympt[oô]mes?|symptoms?",
    "diagnostic": r"diagnostic|diagnosis",
    "remédiation": r"r[eé]m[eé]diation|remediation|mitigation",
    "escalade": r"escalade|escalation",
}


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


# ── L'alerte, soumise à des séries connues ─────────────────────────────────


def _alerte_sonne(projet: Path, tmp_path: Path, erreurs: int, succes: int) -> list[str]:
    """Les instants (en minutes) où promtool voit l'alerte sonner."""
    exiger_outil("docker")
    dossier = tmp_path / f"promtool-{erreurs}"
    dossier.mkdir()
    dossier.chmod(0o755)
    (dossier / "alerts.yaml").write_text((projet / ALERTES).read_text(encoding="utf-8"), encoding="utf-8")
    instants = [30, 60, 90, 120]
    test = {
        "rule_files": ["alerts.yaml"],
        "evaluation_interval": "1m",
        "tests": [
            {
                "interval": "1m",
                "input_series": [
                    {"series": 'http_requests_total{job="notes-api", code="200"}', "values": f"0+{succes}x150"},
                    {"series": 'http_requests_total{job="notes-api", code="500"}', "values": f"0+{erreurs}x150"},
                ],
                "alert_rule_test": [
                    {"eval_time": f"{m}m", "alertname": ALERTE, "exp_alerts": []} for m in instants
                ],
            }
        ],
    }
    (dossier / "test.yaml").write_text(yaml.safe_dump(test), encoding="utf-8")
    for fichier in dossier.iterdir():
        fichier.chmod(0o644)
    res = executer(
        ["docker", "run", "--rm", "-v", f"{dossier}:/w:ro", "-w", "/w", "--entrypoint", "promtool",
         PROMETHEUS, "test", "rules", "test.yaml"],
        timeout=300,
    )
    sortie = res.stdout + res.stderr
    if res.returncode != 0 and "got:" not in sortie:
        pytest.fail(f"promtool refuse vos règles ({ALERTES}) :\n{sortie[-1200:]}")
    return re.findall(rf"alertname: {ALERTE}, time: ([0-9hm]+),\s*\n\s*exp:\[\],\s*\n\s*got:\[\s*\n\s*0:", sortie)


# ── Une référence DORA indépendante, pour des journaux fabriqués ───────────


def _iso(t: dt.datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _journaux(graine: int) -> tuple[list[dict], list[dict]]:
    import random

    # Des journaux de test reproductibles, sans aucun rôle cryptographique.
    hasard = random.Random(graine)  # noqa: S311
    t = dt.datetime(2026, 1, 5, 8, tzinfo=dt.UTC)
    deploiements, incidents = [], []
    for i in range(hasard.randint(6, 14)):
        t += dt.timedelta(days=hasard.randint(1, 9), hours=hasard.randint(0, 9))
        commit = t - dt.timedelta(minutes=hasard.randint(30, 4000))
        sha = f"{graine:04d}{i:036d}"
        deploiements.append({"sha": sha, "committed_at": _iso(commit), "deployed_at": _iso(t), "failed": hasard.random() < 0.15})
        if hasard.random() < 0.25:
            debut = t + dt.timedelta(minutes=hasard.randint(5, 90))
            incidents.append({"deployment_sha": sha, "started_at": _iso(debut),
                              "resolved_at": _iso(debut + dt.timedelta(minutes=hasard.randint(10, 600)))})
    return deploiements, incidents


def _reference(deploiements: list[dict], incidents: list[dict]) -> dict:
    lire = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00"))  # noqa: E731
    dates = sorted(lire(d["deployed_at"]) for d in deploiements)
    semaines = max((dates[-1] - dates[0]).total_seconds() / (7 * 86400), 1.0)
    fautifs = {i["deployment_sha"] for i in incidents}
    duree = [(lire(i["resolved_at"]) - lire(i["started_at"])).total_seconds() / 3600 for i in incidents]
    return {
        "deployments_per_week": round(len(deploiements) / semaines, 2),
        "lead_time_hours_median": round(statistics.median(
            (lire(d["deployed_at"]) - lire(d["committed_at"])).total_seconds() / 3600 for d in deploiements), 2),
        "change_failure_rate": round(sum(1 for d in deploiements if d["failed"] or d["sha"] in fautifs) / len(deploiements), 2),
        "recovery_time_hours_median": round(statistics.median(duree), 2) if duree else None,
    }


# ── Les contrôles ──────────────────────────────────────────────────────────


def test_le_pipeline_verifie_l_alerte_et_mesure_la_livraison(projet: Path) -> None:
    res = jouer_act(projet, "pull_request")
    assert _vert(res), "Sur une pull request, le pipeline doit être vert.\n  " + res.resume()
    assert any(re.search(r"SUCCESS: \d+ rules found", ligne) for ligne in res.lignes), (
        "Le pipeline ne vérifie pas les règles d'alerte (promtool check rules).\n  " + res.resume()
    )
    assert any("deployments_per_week" in ligne for ligne in res.lignes), (
        "Le pipeline ne calcule pas les métriques DORA (scripts/dora.py).\n  " + res.resume()
    )


def test_l_alerte_sonne_quand_le_budget_brule_et_seulement_la(projet: Path, tmp_path: Path) -> None:
    assert (projet / ALERTES).is_file(), f"{ALERTES} est introuvable : rien ne prévient l'astreinte."
    brulure = _alerte_sonne(projet, tmp_path, erreurs=10, succes=90)
    assert brulure and "1h30m" in brulure, (
        f"Avec 10 % d'erreurs pendant deux heures, {ALERTE} ne sonne pas à 1h30 (instants vus : "
        f"{brulure or 'aucun'}) : à ce rythme, le budget de 0,5 % sur 28 jours part en moins de "
        "trois jours, et l'astreinte doit être réveillée."
    )
    calme = _alerte_sonne(projet, tmp_path, erreurs=1, succes=99)
    assert not calme, (
        f"Avec 1 % d'erreurs, {ALERTE} sonne ({calme}) : une alerte qui réveille pour une "
        "consommation lente du budget finit par être ignorée."
    )


def test_les_metriques_dora_sont_justes(projet: Path, tmp_path: Path) -> None:
    script = projet / "scripts" / "dora.py"
    assert script.is_file(), "scripts/dora.py est introuvable."
    for graine in (3, 17, 42):
        deploiements, incidents = _journaux(graine)
        journal_d, journal_i = tmp_path / f"d{graine}.jsonl", tmp_path / f"i{graine}.jsonl"
        journal_d.write_text("".join(json.dumps(d) + "\n" for d in deploiements), encoding="utf-8")
        journal_i.write_text("".join(json.dumps(i) + "\n" for i in incidents), encoding="utf-8")
        res = executer(["python3", str(script), str(journal_d), str(journal_i)], timeout=60)
        assert res.returncode == 0, f"scripts/dora.py échoue :\n{(res.stdout + res.stderr)[-600:]}"
        try:
            obtenu = json.loads(res.stdout)
        except ValueError:
            pytest.fail(f"scripts/dora.py n'écrit pas un objet JSON :\n{res.stdout[-400:]}")
        attendu = _reference(deploiements, incidents)
        for cle, valeur in attendu.items():
            assert obtenu.get(cle) == valeur, (
                f"{cle} vaut {obtenu.get(cle)!r}, la définition du scénario donne {valeur!r} "
                f"({len(deploiements)} déploiements, {len(incidents)} incidents)."
            )


def test_le_runbook_guide_l_astreinte(projet: Path) -> None:
    assert (projet / RUNBOOK).is_file(), f"{RUNBOOK} est introuvable : l'astreinte n'a aucune procédure."
    texte = (projet / RUNBOOK).read_text(encoding="utf-8")
    titres = [x for x in texte.splitlines() if x.startswith("#")]
    for nom, motif in SECTIONS.items():
        assert any(re.search(motif, t, re.I) for t in titres), f"Le runbook n'a pas de section {nom}."
    commandes = re.findall(r"^\s*(kubectl .+)$", texte, re.M)
    assert any("rollout undo" in c for c in commandes), (
        "Le runbook ne dit pas comment revenir à la version précédente (kubectl rollout undo)."
    )
    for commande in commandes:
        assert re.search(r"(-n|--namespace)[ =]notes-api\b", commande), (
            f"Commande sans espace de noms : « {commande.strip()} ». À 3 heures du matin, elle "
            "viserait le mauvais contexte."
        )
        cible = re.search(r"\b(deployment|deploy)/(\S+)", commande)
        assert not cible or cible.group(2) == "notes-api", (
            f"« {commande.strip()} » vise {cible.group(0)}, qui n'existe pas dans deploy/k8s/."
        )
    regles = yaml.safe_load((projet / ALERTES).read_text(encoding="utf-8"))
    alerte = next(
        (r for g in regles.get("groups", []) for r in g.get("rules", []) if r.get("alert") == ALERTE), {}
    )
    lien = str((alerte.get("annotations") or {}).get("runbook_url", ""))
    assert lien.endswith(RUNBOOK.as_posix()), (
        f"L'alerte {ALERTE} ne renvoie pas au runbook (annotation runbook_url : « {lien} »)."
    )


def test_une_regle_cassee_arrete_le_pipeline_et_le_modele_a_jour(projet: Path) -> None:
    with copie_temporaire(projet) as copie:
        fichier = copie / ALERTES
        fichier.write_text(fichier.read_text(encoding="utf-8").replace("rate(", "rat(", 1), encoding="utf-8")
        res = jouer_act(copie, "pull_request")
    assert _rouge(res), (
        "Une copie dont la règle d'alerte ne se parse plus doit rendre le pipeline rouge : une "
        "alerte cassée ne sonne jamais, et personne ne le voit.\n  " + res.resume()
    )
    modele = yaml.safe_load((projet / "threat-model.yml").read_text(encoding="utf-8"))
    visees = [m for m in modele.get("threats", []) if str(m.get("id")) == "T-18"]
    assert visees and visees[0].get("status") == "mitigated", "La menace T-18 passe à `mitigated`."
    assert (projet / str(visees[0].get("evidence") or "")).is_file(), "La preuve de T-18 doit exister."
