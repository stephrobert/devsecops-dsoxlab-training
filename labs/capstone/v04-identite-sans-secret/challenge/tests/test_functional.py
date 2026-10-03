"""V4, une identité sans secret : cinq contrôles, vingt points chacun.

## Ce que ces tests lisent

act ne fournit pas de jeton OIDC : le job de déploiement échoue sous act de la
même façon avec des clés statiques et avec un rôle (« Credentials could not be
loaded », mesuré le 2026-10-03 avec configure-aws-credentials v6.3.0). Un
contrôle qui jouerait le déploiement ne départagerait donc rien.

Les contrôles se répartissent autrement :

- act joue le pipeline sur une BRANCHE DE TRAVAIL et sur une PULL REQUEST :
  les tests passent, et le déploiement ne démarre pas. Un job sauté n'écrit
  aucun résultat dans la sortie JSON d'act ;
- les workflows et l'infrastructure sont relus : aucune clé statique, un
  jeton OIDC pour le seul job qui déploie ;
- la politique de confiance du rôle est ÉVALUÉE contre les jetons que GitHub
  émettrait dans cinq situations : seul un push sur main de acme/notes-api
  doit pouvoir endosser le rôle.

## L'évaluateur

Il couvre ce qu'une politique de confiance OIDC emploie : `Effect`,
`Principal.Federated`, `Action`, et les opérateurs `StringEquals` et
`StringLike` (jokers `*` et `?`), clé à valeur simple ou liste. Un opérateur
qu'il ne connaît pas est refusé par un message, jamais ignoré : l'ignorer
reviendrait à accepter une condition qu'il n'a pas vérifiée.
"""

from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path

import pytest
import yaml

from conftest import (
    exiger_application,
    exiger_workdir,
    exiger_workflows,
    jouer_act,
    lire_workflows,
    references_uses,
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)
LAB_ID = "capstone-v04-identite-sans-secret"
FOURNISSEUR = "token.actions.githubusercontent.com"
CONFIGURE_AWS = "aws-actions/configure-aws-credentials"
ENTREES_STATIQUES = {"aws-access-key-id", "aws-secret-access-key", "aws-session-token"}
OPERATEURS = {"StringEquals", "StringLike"}


@pytest.fixture(scope="module")
def projet() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    exiger_application(WORKDIR)
    exiger_workflows(WORKDIR)
    return WORKDIR


def _jobs_de_deploiement(projet: Path) -> list[tuple[str, str, dict]]:
    """(fichier, id, job) de chaque job qui s'authentifie auprès d'AWS."""
    trouves = []
    for fichier, workflow in lire_workflows(projet).items():
        for ident, job in (workflow.get("jobs") or {}).items():
            pas = job.get("steps") or []
            if any(str(p.get("uses", "")).startswith(CONFIGURE_AWS) for p in pas if isinstance(p, dict)):
                trouves.append((fichier, ident, job))
    return trouves


def _exiger_deploiement(projet: Path) -> tuple[str, str, dict]:
    jobs = _jobs_de_deploiement(projet)
    assert jobs, (
        "Plus aucun job ne s'authentifie auprès d'AWS : notes-api doit toujours être "
        f"publiée. Le job de déploiement garde son étape {CONFIGURE_AWS}."
    )
    return jobs[0]


# ── L'évaluateur de politique de confiance ─────────────────────────────────


def _liste(valeur) -> list:
    return valeur if isinstance(valeur, list) else [valeur]


def _condition_tenue(operateur: str, attendu, jeton: dict) -> bool:
    if operateur not in OPERATEURS:
        pytest.fail(
            f"La politique emploie l'opérateur {operateur}, que ce contrôle ne sait pas "
            f"évaluer. Exprimez les conditions avec {' ou '.join(sorted(OPERATEURS))}."
        )
    for cle, valeurs in attendu.items():
        nom = cle.split(":", 1)[1] if cle.startswith(FOURNISSEUR + ":") else None
        if nom is None or nom not in jeton:
            return False
        reel = jeton[nom]
        if operateur == "StringEquals":
            if reel not in _liste(valeurs):
                return False
        elif not any(fnmatch.fnmatchcase(reel, motif) for motif in _liste(valeurs)):
            return False
    return True


def peut_endosser(politique: dict, jeton: dict, fournisseur_arn: str) -> bool:
    """Vrai si une déclaration Allow accepte ce jeton, et qu'aucun Deny ne le refuse."""
    autorise = False
    for declaration in _liste(politique.get("Statement", [])):
        actions = _liste(declaration.get("Action", []))
        if "sts:AssumeRoleWithWebIdentity" not in actions and "sts:*" not in actions:
            continue
        federes = _liste((declaration.get("Principal") or {}).get("Federated", []))
        if fournisseur_arn not in federes:
            continue
        conditions = declaration.get("Condition") or {}
        if all(_condition_tenue(op, attendu, jeton) for op, attendu in conditions.items()):
            if declaration.get("Effect") == "Deny":
                return False
            if declaration.get("Effect") == "Allow":
                autorise = True
    return autorise


def _jeton(sub: str, aud: str = "sts.amazonaws.com", depot: str = "acme/notes-api") -> dict:
    return {"sub": sub, "aud": aud, "repository": depot}


SITUATIONS = [
    ("un push sur main de acme/notes-api", _jeton("repo:acme/notes-api:ref:refs/heads/main"), True),
    ("un push sur une branche de travail", _jeton("repo:acme/notes-api:ref:refs/heads/feature"), False),
    ("une pull request, y compris d'un fork", _jeton("repo:acme/notes-api:pull_request"), False),
    (
        "un push sur main d'un AUTRE dépôt",
        _jeton("repo:acme/notes-api-fork:ref:refs/heads/main", depot="acme/notes-api-fork"),
        False,
    ),
    (
        "un jeton destiné à un autre service que STS",
        _jeton("repo:acme/notes-api:ref:refs/heads/main", aud="https://github.com/acme"),
        False,
    ),
]


# ── Les contrôles ──────────────────────────────────────────────────────────


def test_ni_une_branche_ni_une_pull_request_ne_deploient(projet: Path) -> None:
    fichier, ident, _job = _exiger_deploiement(projet)
    branche = jouer_act(projet, "push", payload={"ref": "refs/heads/feature"})
    pr = jouer_act(projet, "pull_request")
    for nom, res in (("un push sur la branche feature", branche), ("une pull request", pr)):
        autres = [j for j in res.jobs if j != ident]
        assert autres and all(res.job(j) == "success" for j in autres), (
            f"Sur {nom}, les tests doivent rester verts.\n  " + res.resume()
        )
        assert any(re.search(r"\b\d+ passed\b.* in [0-9.]+s", ligne) for ligne in res.lignes), (
            f"Sur {nom}, les tests de l'application ne tournent plus.\n  " + res.resume()
        )
        assert ident not in res.jobs, (
            f"Sur {nom}, le job `{ident}` de {fichier} démarre : seul un push sur main "
            "publie une version. Une branche ou une pull request qui déploient sont la "
            "porte d'entrée que la politique de confiance devra fermer de son côté.\n  "
            + res.resume()
        )


def test_aucune_cle_statique_ni_dans_le_pipeline_ni_dans_l_infra(projet: Path) -> None:
    for fichier in exiger_workflows(projet):
        texte = fichier.read_text(encoding="utf-8")
        secrets = sorted(set(re.findall(r"secrets\.(\w+)", texte)) - {"GITHUB_TOKEN"})
        assert not secrets, (
            f"{fichier.relative_to(projet)} lit encore {', '.join(secrets)} : un secret de "
            "dépôt est une clé de longue durée, que tout job qui la reçoit peut exfiltrer."
        )
    for _fichier, ident, job in _jobs_de_deploiement(projet):
        for pas in job.get("steps") or []:
            if isinstance(pas, dict) and str(pas.get("uses", "")).startswith(CONFIGURE_AWS):
                statiques = sorted(ENTREES_STATIQUES & set(pas.get("with") or {}))
                assert not statiques, (
                    f"Le job `{ident}` passe encore {', '.join(statiques)} à {CONFIGURE_AWS}."
                )
    infra = "\n".join(p.read_text(encoding="utf-8") for p in sorted((projet / "infra").glob("*.tf")))
    for ressource in ("aws_iam_access_key", "aws_iam_user"):
        assert not re.search(rf'resource\s+"{ressource}"', infra), (
            f"infra/ déclare encore une ressource {ressource} : tant que l'utilisateur et "
            "sa clé existent, la clé copiée dans les secrets reste valable. La supprimer "
            "du code, c'est la révoquer au prochain apply."
        )


def test_seul_le_job_de_deploiement_obtient_un_jeton_oidc(projet: Path) -> None:
    fichier, ident, job = _exiger_deploiement(projet)
    workflow = lire_workflows(projet)[fichier]
    assert "id-token" not in (workflow.get("permissions") or {}), (
        f"{fichier} accorde id-token au niveau du workflow : chaque job pourrait alors "
        "demander un jeton. La permission se déclare sur le seul job qui déploie."
    )
    assert (job.get("permissions") or {}).get("id-token") == "write", (
        f"Le job `{ident}` ne déclare pas `id-token: write` : sans elle, GitHub ne lui "
        "remet aucun jeton OIDC à échanger contre des identifiants."
    )
    for autre_fichier, autre in lire_workflows(projet).items():
        for autre_id, autre_job in (autre.get("jobs") or {}).items():
            if (autre_fichier, autre_id) != (fichier, ident):
                assert (autre_job.get("permissions") or {}).get("id-token") != "write", (
                    f"Le job `{autre_id}` de {autre_fichier} obtient aussi un jeton OIDC."
                )
    pas = next(p for p in job["steps"] if str(p.get("uses", "")).startswith(CONFIGURE_AWS))
    assert str((pas.get("with") or {}).get("role-to-assume", "")).startswith("arn:aws:iam::"), (
        f"L'étape {CONFIGURE_AWS} doit nommer le rôle à endosser (`role-to-assume`)."
    )
    refs = [r for r in references_uses(projet) if r.action == CONFIGURE_AWS]
    assert refs and all(r.epinglee_par_sha for r in refs), (
        f"{CONFIGURE_AWS} reçoit le jeton OIDC : il s'épingle par SHA de commit, comme "
        "chaque action du pipeline."
    )


def test_la_politique_de_confiance_n_accepte_que_main(projet: Path) -> None:
    infra = "\n".join(p.read_text(encoding="utf-8") for p in sorted((projet / "infra").glob("*.tf")))
    m = re.search(r'assume_role_policy\s*=\s*file\(\s*"\$\{path\.module\}/([^"]+\.json)"\s*\)', infra)
    assert m, (
        "Le rôle de déploiement lit sa politique de confiance dans un fichier JSON du "
        'dossier infra : assume_role_policy = file("${path.module}/<fichier>.json"). '
        "Un fichier à part se relit et se teste."
    )
    chemin = projet / "infra" / m.group(1)
    assert chemin.is_file(), f"infra/{m.group(1)} est introuvable."
    politique = json.loads(chemin.read_text(encoding="utf-8"))
    fournisseurs = {
        f for d in _liste(politique.get("Statement", []))
        for f in _liste((d.get("Principal") or {}).get("Federated", []))
        if str(f).endswith(f"oidc-provider/{FOURNISSEUR}")
    }
    assert fournisseurs, f"La politique ne fait confiance à aucun fournisseur OIDC {FOURNISSEUR}."
    arn = sorted(fournisseurs)[0]
    for situation, jeton, attendu in SITUATIONS:
        assert peut_endosser(politique, jeton, arn) is attendu, (
            f"Pour {situation} (sub = {jeton['sub']}, aud = {jeton['aud']}), la politique "
            + ("refuse le rôle : le déploiement de main échouerait." if attendu else
               "ACCEPTE le rôle : n'importe quel job de ce contexte publierait une version.")
        )


def test_le_modele_dit_la_cle_retiree_et_sa_preuve(projet: Path) -> None:
    modele = yaml.safe_load((projet / "threat-model.yml").read_text(encoding="utf-8"))
    visees = [m for m in modele.get("threats", []) if str(m.get("id")) == "T-12"]
    assert visees, "Le modèle ne porte plus la menace T-12 sur les identifiants de déploiement."
    menace = visees[0]
    assert menace.get("status") == "mitigated", (
        "La clé statique a disparu : la menace T-12 passe à `mitigated`."
    )
    preuve = projet / str(menace.get("evidence") or "")
    assert preuve.is_file() and FOURNISSEUR in preuve.read_text(encoding="utf-8"), (
        "La preuve de T-12 doit être le fichier qui la démontre : la politique de "
        "confiance du rôle, qui nomme le fournisseur OIDC de GitHub."
    )
