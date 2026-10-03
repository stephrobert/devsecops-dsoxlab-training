"""
Configuration pytest globale pour le repo devsecops-dsoxlab-training.

Le catalogue est un FIL ROUGE : l'apprenant fait évoluer un seul projet,
`notes-api`, de V0 (un pipeline minimal) à V11 (des métriques DORA). Le point
de départ d'un lab est la solution du précédent, et les tests jugent l'état du
dépôt de l'apprenant, jamais les commandes tapées.

Les labs sont de type `shell` : ils s'exécutent dans `challenge/work` sur la
machine de l'apprenant. Les tests jouent son pipeline avec act, dans l'image du
runner épinglée par digest, et lisent ce qu'il produit ; les propriétés qui
sont dans le texte (permissions, épinglage, déclencheurs) se lisent dans le
YAML. Un test qui doit voir le pipeline échouer modifie une COPIE du projet.

Helpers communs exposés aux tests : `workdir_lab()`, `exiger_workdir()`,
`exiger_application()`, `jouer_act()`, `copie_temporaire()`,
`lire_workflows()`, `references_uses()`.

Le suivi d'avancement est assuré par la CLI dsoxlab externe
(`uv tool install dsoxlab`), qui enregistre les résultats de `dsoxlab check`
dans `<repo>/.dsoxlab.db`.
"""

import contextlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent
LABS_ROOT = REPO_ROOT / "labs"
SOLUTIONS_ROOT = REPO_ROOT / "solution"
VAULT_PASS = REPO_ROOT / ".vault-pass"

# Le cœur de notes-api : il reste à cet endroit d'une version à l'autre, sinon
# les fixtures du lab suivant ne s'appliquent plus.
APPLICATION = Path("src") / "notes_api" / "app.py"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "no_replay: le lab s'orchestre lui-même, ne pas rejouer la solution "
        "de référence avant ses tests (voir la fixture _apply_lab_state).",
    )


def workdir_lab(fichier_test: str | Path) -> Path:
    """Workdir du lab auquel appartient un fichier de test.

    Par défaut `<lab>/challenge/work`. La variable d'environnement
    `LAB_WORKDIR` la surcharge, ce dont se sert `scripts/verify-solutions.py`
    pour rejouer les mêmes tests contre la solution de référence.
    """
    surcharge = os.environ.get("LAB_WORKDIR")
    if surcharge:
        return Path(surcharge)
    return Path(fichier_test).resolve().parents[2] / "challenge" / "work"


def exiger_workdir(workdir: Path, lab_id: str) -> None:
    """Arrête proprement le test quand le workdir n'existe pas.

    La distinction est volontaire, et c'est elle qui rend la suite lisible :

    - **lab simplement pas joué** : on SKIPPE. Un `pytest` lancé à la racine du
      dépôt ne doit pas afficher des erreurs rouges pour des labs que personne
      n'a ouverts.
    - **workdir surchargé par `LAB_WORKDIR`** : on ÉCHOUE. Dans ce cas le
      répertoire devait être matérialisé par l'appelant, son absence est un
      vrai défaut et non un lab au repos.
    """
    if workdir.is_dir():
        return
    if os.environ.get("LAB_WORKDIR"):
        pytest.fail(
            f"LAB_WORKDIR pointe sur {workdir}, qui n'existe pas. "
            "L'appelant devait matérialiser ce répertoire avant de lancer les "
            "tests."
        )
    pytest.skip(
        f"Lab non joué : {workdir} est absent. "
        f"Lancez `dsoxlab run {lab_id}` pour poser l'état de départ."
    )




def exiger_application(workdir: Path) -> None:
    """Le cœur de notes-api est à sa place : sinon le fil rouge est rompu."""
    if not (workdir / APPLICATION).is_file():
        pytest.fail(
            f"{APPLICATION} est absent de {workdir}. C'est l'application que le "
            "fil rouge fait évoluer : elle doit rester à cet emplacement.",
            pytrace=False,
        )


# ── Rejeu de la solution de référence avant les tests (mode formateur) ───────
#
# Même mécanisme que le dépôt ansible-training : une fixture autouse pose l'état
# de départ de chaque lab (fixtures + solution déchiffrée) dans `challenge/work`
# AVANT ses tests, de sorte que `pytest labs/` (via scripts/test-all.sh) joue
# réellement TOUS les labs au lieu de tous les skipper : « poser la solution »
# = copier les fixtures puis déchiffrer la solution par-dessus.


def _dechiffrer(fichier: Path) -> bytes:
    """Contenu en clair d'un fichier de solution chiffré par ansible-vault."""
    proc = subprocess.run(
        ["ansible-vault", "view", "--vault-password-file", str(VAULT_PASS), str(fichier)],
        capture_output=True, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Déchiffrement impossible pour {fichier.name} : "
            f"{proc.stderr.decode(errors='replace').strip()}"
        )
    return proc.stdout


SCRIPT_SOLUTION = "solution.sh"


def _jouer_script_de_solution(work: Path) -> None:
    """Exécute `solution.sh` s'il a été posé, puis le retire du workdir.

    Certains labs ne se corrigent PAS en écrivant des fichiers. « Enregistre un
    plan avec `-out`, relis-le en JSON, applique ce plan-là » produit des
    artefacts qui dépendent du state : aucune solution faite de fichiers ne peut
    les fournir, et le sens « 100 » de ces labs n'était donc pas jouable.

    Le script est chiffré comme le reste de la solution, joué DANS le workdir,
    et retiré ensuite : il est le moyen d'atteindre l'état attendu, il n'en fait
    pas partie. Un test qui le trouverait encore là mesurerait le mauvais objet.

    Son échec est bruyant. Une solution de référence qui casse en silence
    rendrait tous les tests du lab rouges sans dire pourquoi, et c'est
    exactement le genre de diagnostic qui coûte une journée.
    """
    script = work / SCRIPT_SOLUTION
    if not script.is_file():
        return
    proc = subprocess.run(
        ["bash", SCRIPT_SOLUTION],
        cwd=work, capture_output=True, text=True, check=False,
    )
    script.unlink()
    if proc.returncode != 0:
        raise RuntimeError(
            f"La solution de référence a échoué (code {proc.returncode}).\n"
            f"--- stdout ---\n{proc.stdout[-2000:]}\n"
            f"--- stderr ---\n{proc.stderr[-2000:]}"
        )


def _materialiser_solution(lab_root: Path) -> None:
    """Copie les fixtures, déchiffre la solution, puis joue son script.

    Reproduit à l'identique l'aplatissement du runtime shell de dsoxlab et le
    comportement de scripts/verify-solutions.py, mais dans le workdir réel.
    """
    work = lab_root / "challenge" / "work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    fixtures = lab_root / "fixtures"
    if fixtures.is_dir():
        for fichier in sorted(fixtures.rglob("*")):
            if fichier.is_file():
                cible = work / fichier.relative_to(fixtures)
                cible.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(fichier, cible)

    lab_rel = lab_root.relative_to(LABS_ROOT)
    sol_dir = SOLUTIONS_ROOT / lab_rel
    for chiffre in sorted(sol_dir.rglob("*")):
        if chiffre.is_file():
            cible = work / chiffre.relative_to(sol_dir)
            cible.parent.mkdir(parents=True, exist_ok=True)
            cible.write_bytes(_dechiffrer(chiffre))

    _jouer_script_de_solution(work)


@pytest.fixture(scope="module", autouse=True)
def _apply_lab_state(request: pytest.FixtureRequest) -> None:
    """Pose la solution de référence du lab avant ses tests (mode formateur).

    Désactivée dans trois cas, à ne pas confondre :

    - `LAB_NO_REPLAY=1` : mode APPRENANT, posé par `dsoxlab check`. On note le
      travail de l'apprenant, on ne rejoue rien par-dessus.
    - `LAB_WORKDIR` défini : `scripts/verify-solutions.py` matérialise déjà la
      solution dans son propre répertoire temporaire, il ne faut pas toucher au
      `challenge/work` de l'apprenant en parallèle.
    - marqueur `@pytest.mark.no_replay` : le lab s'orchestre lui-même.

    No-op quand le lab n'a pas de solution de référence sous `solution/` (labs
    squelette) : leurs tests skippent d'eux-mêmes.
    """
    if os.environ.get("LAB_NO_REPLAY") == "1":
        return
    if os.environ.get("LAB_WORKDIR"):
        return
    if request.node.get_closest_marker("no_replay"):
        return

    test_path = Path(str(request.fspath)).resolve()
    # <lab>/challenge/tests/test_*.py → parents[2] == <lab>
    lab_root = test_path.parents[2]
    if not (lab_root / "lab.yaml").is_file():
        return
    if not (SOLUTIONS_ROOT / lab_root.relative_to(LABS_ROOT)).is_dir():
        return  # lab sans solution de référence : le test skippe de lui-même

    if not VAULT_PASS.is_file():
        pytest.skip(
            ".vault-pass absent : la solution chiffrée ne peut pas être rejouée."
        )
    _materialiser_solution(lab_root)


# --- Jouer un workflow avec act ------------------------------------------------
#
# Repris de github-actions-training/conftest.py, éprouvé là-bas sur act 0.2.89
# et l'image du runner épinglée par digest. Toute évolution se fait d'abord
# dans le catalogue GitHub Actions, puis se reporte ici.

LABEL_RUNNER = "ubuntu-24.04"
IMAGE_RUNNER = (
    "catthehacker/ubuntu:act-24.04"
    "@sha256:c58e2b364da03b0c804c7d660f2ecbedf2f221a382b9baa0b344b0144780ff43"
)


_images_verifiees: set[str] = set()


def exiger_outil(nom: str) -> str:
    """Le chemin de l'outil, ou un échec qui dit comment l'installer."""
    chemin = shutil.which(nom)
    if not chemin:
        pytest.fail(
            f"L'outil `{nom}` n'est pas sur le PATH. Il est épinglé dans "
            "mise.toml à la racine du catalogue : lancez `mise install`, puis "
            "rejouez `dsoxlab check`."
        )
    return chemin


def executer(
    cmd: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 300,
    entree: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Lance une commande et rend le résultat sans lever : c'est le test qui juge."""
    environnement = dict(os.environ)
    if env:
        environnement.update(env)
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            env=environnement,
            capture_output=True,
            text=True,
            timeout=timeout,
            input=entree,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        sortie = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        return subprocess.CompletedProcess(cmd, 124, stdout=sortie, stderr=f"délai de {timeout} s dépassé")


# Ce qu'on ne copie jamais d'un répertoire de travail : le dépôt git de
# l'apprenant (act en reçoit un neuf), les caches Python et pytest.
EXCLUS_COPIE = (".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache")


@contextlib.contextmanager
def copie_temporaire(depot: Path) -> Iterator[Path]:
    """Une copie du répertoire de travail, à modifier ou à jouer, détruite à la sortie."""
    with tempfile.TemporaryDirectory(prefix="lab-gha-") as tmp:
        cible = Path(tmp) / "depot"
        shutil.copytree(depot, cible, ignore=shutil.ignore_patterns(*EXCLUS_COPIE), symlinks=True)
        yield cible


def _git(*args: str, cwd: Path) -> None:
    cmd = [
        "git",
        "-c", "user.name=lab",
        "-c", "user.email=lab@example.invalid",
        "-c", "commit.gpgsign=false",
        "-c", "init.defaultBranch=main",
        *args,
    ]
    res = executer(cmd, cwd=cwd, timeout=60)
    if res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} a échoué : {res.stderr.strip()}")


def initialiser_git(depot: Path) -> None:
    """act déduit le contexte (ref, sha, dépôt) d'un dépôt git : on lui en donne un neuf."""
    _git("init", "-q", "-b", "main", cwd=depot)
    _git("add", "-A", cwd=depot)
    _git("commit", "-q", "--allow-empty", "-m", "point de depart", cwd=depot)


def image_prete() -> None:
    """L'image du runner est présente, sinon on la tire une fois, par digest."""
    if IMAGE_RUNNER in _images_verifiees:
        return
    if executer(["docker", "image", "inspect", IMAGE_RUNNER], timeout=60).returncode != 0:
        res = executer(["docker", "pull", IMAGE_RUNNER], timeout=900)
        if res.returncode != 0:
            pytest.fail(
                f"Impossible de tirer l'image du runner {IMAGE_RUNNER} : "
                f"{res.stderr.strip()[-400:]}. Docker doit répondre (`docker info`) ; "
                "act ne joue rien sans lui."
            )
    _images_verifiees.add(IMAGE_RUNNER)


# ── act ──────────────────────────────────────────────────────────────────────


@dataclass
class ResultatAct:
    """Ce qu'act a produit, lu depuis sa sortie `--json`."""

    commande: list[str]
    rc: int
    jobs: dict[str, list[str]] = field(default_factory=dict)  # jobID -> résultats
    lignes: list[str] = field(default_factory=list)  # tout ce que les steps ont écrit
    lignes_par_job: dict[str, list[str]] = field(default_factory=dict)
    steps: list[dict[str, str | None]] = field(default_factory=list)
    erreurs: list[str] = field(default_factory=list)
    brut: str = ""

    def job(self, identifiant: str) -> str | None:
        """Le résultat d'un job : `success`, `failure`, ou `None` s'il n'a pas été joué."""
        resultats = self.jobs.get(identifiant) or []
        if not resultats:
            return None
        if len(resultats) == 1:
            return resultats[0]
        # Une matrice produit plusieurs jobs sous le même identifiant : on rend
        # `failure` dès qu'un seul a échoué, c'est ce que GitHub affiche.
        return "failure" if "failure" in resultats else resultats[0]

    @property
    def sortie(self) -> str:
        return "\n".join(self.lignes)

    def contient(self, texte: str) -> bool:
        return texte in self.brut

    def resume(self, n: int = 12) -> str:
        """Un extrait pour les messages d'assertion : jobs, erreurs, dernières lignes."""
        parts = [f"commande : {' '.join(self.commande)}", f"code de retour : {self.rc}"]
        if self.jobs:
            etats = ", ".join(f"{j}={'/'.join(r)}" for j, r in sorted(self.jobs.items()))
            parts.append(f"jobs : {etats}")
        else:
            parts.append("jobs : aucun job n'a été joué")
        if self.erreurs:
            parts.append("erreurs d'act :\n    " + "\n    ".join(e.strip() for e in self.erreurs[-4:]))
        if self.lignes:
            parts.append("dernières lignes écrites :\n    " + "\n    ".join(self.lignes[-n:]))
        return "\n  ".join(parts)


def jouer_act(
    depot: Path,
    evenement: str = "push",
    *,
    workflow: str | None = None,
    job: str | None = None,
    payload: dict | None = None,
    timeout: int = 600,
) -> ResultatAct:
    """Joue un workflow avec act dans une copie neuve du répertoire de travail.

    `workflow` est un chemin relatif au dépôt (`.github/workflows/ci.yml`),
    `job` un identifiant de job, `payload` le corps de l'événement (`-e`).

    Aucun secret ni variable n'est passé à act : écrire des secrets dans un
    fichier, même en 0600, est ce que CodeQL signale à raison
    (py/clear-text-storage-sensitive-data). Un lab qui a besoin d'un secret
    le simule autrement.
    """
    exiger_outil("act")
    image_prete()
    with copie_temporaire(depot) as d:
        initialiser_git(d)
        aux = d.parent
        cmd = [
            "act", evenement, "--json", "--pull=false",
            "-P", f"{LABEL_RUNNER}={IMAGE_RUNNER}",
            "--artifact-server-path", str(aux / "artefacts"),
            "--cache-server-path", str(aux / "cache"),
        ]
        if workflow:
            cmd += ["-W", workflow]
        if job:
            cmd += ["-j", job]
        if payload is not None:
            (aux / "event.json").write_text(json.dumps(payload), encoding="utf-8")
            cmd += ["-e", str(aux / "event.json")]
        res = executer(cmd, cwd=d, env={"ACT_DISABLE_VERSION_CHECK": "1"}, timeout=timeout)
        brut = res.stdout + res.stderr
    return _lire_json_act(cmd, res.returncode, brut)


def _lire_json_act(cmd: list[str], rc: int, brut: str) -> ResultatAct:
    res = ResultatAct(commande=cmd, rc=rc, brut=brut)
    for ligne in brut.splitlines():
        try:
            obj = json.loads(ligne)
        except ValueError:
            continue
        if not isinstance(obj, dict):
            continue
        msg = str(obj.get("msg", ""))
        job_id = obj.get("jobID") or obj.get("job") or "?"
        if obj.get("raw_output"):
            for ecrite in msg.split("\n"):
                if ecrite == "" and msg.endswith("\n"):
                    continue
                res.lignes.append(ecrite)
                res.lignes_par_job.setdefault(job_id, []).append(ecrite)
        if obj.get("jobResult"):
            res.jobs.setdefault(job_id, []).append(str(obj["jobResult"]))
        if obj.get("stepResult"):
            res.steps.append({"job": job_id, "step": obj.get("step"), "resultat": str(obj["stepResult"])})
        if obj.get("level") == "error":
            res.erreurs.append(msg)
    if rc != 0 and not res.erreurs and not res.jobs:
        # act a refusé avant de jouer (workflow invalide, aucun job) : la
        # raison est dans la sortie brute.
        res.erreurs.append(brut.strip()[-600:])
    return res


# ── Lecture statique des workflows (compléments) ────────────────────────────


def fichiers_workflows(depot: Path) -> list[Path]:
    dossier = depot / ".github" / "workflows"
    if not dossier.is_dir():
        return []
    return sorted(p for p in dossier.iterdir() if p.suffix in (".yml", ".yaml"))


def exiger_workflows(depot: Path) -> list[Path]:
    fichiers = fichiers_workflows(depot)
    if not fichiers:
        pytest.fail(
            "Aucun fichier `.github/workflows/*.yml` dans le répertoire de travail : "
            "GitHub ne cherche les workflows que dans ce dossier, avec le point devant "
            "`.github` et l'extension .yml ou .yaml. Rien ne peut tourner tant qu'il "
            "n'existe pas."
        )
    return fichiers


def lire_workflows(depot: Path) -> dict[str, dict]:
    """Chaque workflow, analysé. Un YAML invalide est un échec qui nomme le fichier."""
    resultat: dict[str, dict] = {}
    for fichier in exiger_workflows(depot):
        try:
            donnees = yaml.safe_load(fichier.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            pytest.fail(
                f"{fichier.relative_to(depot)} n'est pas un YAML valide : {exc}. "
                "GitHub l'ignorerait, avec une erreur dans l'onglet Actions."
            )
        if not isinstance(donnees, dict):
            pytest.fail(f"{fichier.relative_to(depot)} ne contient pas un workflow (dictionnaire attendu).")
        resultat[str(fichier.relative_to(depot))] = donnees
    return resultat


def declencheurs(workflow: dict) -> set[str]:
    """Les événements d'un workflow. PyYAML lit la clé `on` comme le booléen True."""
    valeur = workflow.get("on", workflow.get(True))
    if valeur is None:
        return set()
    if isinstance(valeur, str):
        return {valeur}
    if isinstance(valeur, list):
        return {str(v) for v in valeur}
    if isinstance(valeur, dict):
        return {str(k) for k in valeur}
    return set()


@dataclass(frozen=True)
class ReferenceUses:
    fichier: str
    ligne: int
    action: str  # owner/repo ou owner/repo/chemin
    ref: str | None  # ce qui suit le @
    commentaire: str | None  # ce qui suit le #

    @property
    def locale(self) -> bool:
        return self.action.startswith("./") or self.action.startswith("docker://")

    @property
    def epinglee_par_sha(self) -> bool:
        return bool(self.ref) and re.fullmatch(r"[0-9a-f]{40}", self.ref or "") is not None


_RE_USES = re.compile(r"^\s*-?\s*uses:\s*['\"]?([^\s'\"#]+)['\"]?\s*(?:#\s*(.*?)\s*)?$")


def references_uses(depot: Path) -> list[ReferenceUses]:
    """Chaque `uses:` des workflows, lu dans le texte pour garder le commentaire."""
    refs: list[ReferenceUses] = []
    for fichier in fichiers_workflows(depot):
        for numero, texte in enumerate(fichier.read_text(encoding="utf-8").splitlines(), 1):
            m = _RE_USES.match(texte)
            if not m:
                continue
            cible, commentaire = m.group(1), m.group(2)
            action, _, ref = cible.partition("@")
            refs.append(
                ReferenceUses(
                    fichier=str(fichier.relative_to(depot)),
                    ligne=numero,
                    action=action,
                    ref=ref or None,
                    commentaire=commentaire or None,
                )
            )
    return refs
