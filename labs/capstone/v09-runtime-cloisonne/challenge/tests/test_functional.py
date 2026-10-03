"""V9, l'exécution cloisonnée : cinq contrôles, vingt points chacun.

## Ce que ces tests font

Ils montent un cluster kind Kubernetes 1.37, dont le CNI par défaut, kindnet,
applique les NetworkPolicies. Ils construisent l'image de notes-api depuis
VOTRE Dockerfile, la chargent dans les nœuds, et appliquent vos manifestes de
`deploy/k8s/` : seule l'image du conteneur notes-api est remplacée par celle
qui vient d'être construite.

Ils posent ensuite trois Pods de contrôle : un client dans l'espace de noms
`ingress`, celui du contrôleur d'entrée ; un client dans `default` ; et un
petit serveur HTTP dans `default`, que notes-api ne doit pas pouvoir joindre.
Le trafic est mesuré pour de vrai, avec un délai court : une connexion qui
n'aboutit pas en cinq secondes est une connexion refusée.

Comptez trois à quatre minutes.
"""

from __future__ import annotations

import secrets
from pathlib import Path

import pytest
import yaml

from conftest import (
    IMAGE_BASE_BANC,
    banc_kind_kyverno,
    executer,
    exiger_workdir,
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)
LAB_ID = "capstone-v09-runtime-cloisonne"
MANIFESTES = Path("deploy") / "k8s"
CLIENT = "banc-client:1"
SONDE_SORTIE = (
    "import socket\n"
    "try:\n"
    "    adresse = socket.getaddrinfo('cible.default.svc.cluster.local', 8080)[0][4][0]\n"
    "except OSError as exc:\n"
    "    print('DNS-KO', exc); raise SystemExit\n"
    "s = socket.socket(); s.settimeout(5)\n"
    "try:\n"
    "    s.connect((adresse, 8080)); print('SORTIE-OUVERTE')\n"
    "except OSError:\n"
    "    print('SORTIE-FERMEE')\n"
)


def _documents(projet: Path) -> list[dict]:
    docs: list[dict] = []
    for fichier in sorted((projet / MANIFESTES).glob("*.y*ml")):
        docs.extend(d for d in yaml.safe_load_all(fichier.read_text(encoding="utf-8")) if isinstance(d, dict))
    return docs


@pytest.fixture(scope="module")
def projet() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    if not list((WORKDIR / MANIFESTES).glob("*.y*ml")):
        pytest.fail(f"Aucun manifeste dans {MANIFESTES}/ : rien à déployer.")
    return WORKDIR


@pytest.fixture(scope="module")
def cluster(projet: Path):
    etiquette = f"notes-api-controle:v09-{secrets.token_hex(4)}"
    res = executer(["docker", "build", "-q", "-t", etiquette, "."], cwd=projet, timeout=900)
    if res.returncode != 0:
        pytest.fail("L'image du projet ne se construit pas :\n" + (res.stdout + res.stderr)[-1500:])
    # L'image cliente se CONSTRUIT : busybox tirée par digest est un index
    # multi-plateforme dont seule la plateforme locale est présente, et
    # `kind load` échoue alors sur « content digest ... not found ».
    res = executer(
        ["docker", "build", "-q", "-t", CLIENT, "-"], entree=f"FROM {IMAGE_BASE_BANC}\n", timeout=300
    )
    if res.returncode != 0:
        pytest.fail("L'image cliente du banc ne se construit pas :\n" + (res.stdout + res.stderr)[-800:])
    try:
        with banc_kind_kyverno("v09", kyverno=False) as banc:
            banc.charger_image(etiquette)
            banc.charger_image(CLIENT)
            docs = _documents(projet)
            for doc in docs:
                if doc.get("kind") == "Deployment":
                    for conteneur in doc["spec"]["template"]["spec"].get("containers", []):
                        if conteneur.get("name") == "notes-api":
                            conteneur["image"] = etiquette
                            conteneur["imagePullPolicy"] = "IfNotPresent"
            espaces = [d for d in docs if d.get("kind") == "Namespace"]
            autres = [d for d in docs if d.get("kind") != "Namespace"]
            banc.appliquer(yaml.safe_dump_all(espaces))
            banc.appliquer(yaml.safe_dump_all(autres))
            banc.appliquer(_pods_de_controle())
            deploiement = banc.kubectl(
                "-n", "notes-api", "rollout", "status", "deployment/notes-api", "--timeout=180s", timeout=200
            )
            for ns, nom in (("ingress", "client"), ("default", "client"), ("default", "cible")):
                banc.kubectl("-n", ns, "wait", f"pod/{nom}", "--for=condition=Ready", "--timeout=120s", timeout=130)
            yield banc, deploiement
    finally:
        executer(["docker", "rmi", "-f", etiquette, CLIENT], timeout=120)


def _pods_de_controle() -> str:
    pod = """\
apiVersion: v1
kind: Pod
metadata:
  name: {nom}
  namespace: {ns}
  labels:
    app: {nom}
spec:
  containers:
    - name: {nom}
      image: {image}
      imagePullPolicy: IfNotPresent
      command: {commande}
"""
    service = """\
apiVersion: v1
kind: Service
metadata:
  name: cible
  namespace: default
spec:
  selector:
    app: cible
  ports:
    - port: 8080
      targetPort: 8080
"""
    return "---\n".join([
        "apiVersion: v1\nkind: Namespace\nmetadata:\n  name: ingress\n",
        pod.format(nom="client", ns="ingress", image=CLIENT, commande='["sleep", "3600"]'),
        pod.format(nom="client", ns="default", image=CLIENT, commande='["sleep", "3600"]'),
        pod.format(nom="cible", ns="default", image=CLIENT, commande='["httpd", "-f", "-p", "8080"]'),
        service,
    ])


def _joindre_l_api(banc, ns: str) -> tuple[bool, str]:
    res = banc.kubectl(
        "-n", ns, "exec", "client", "--", "wget", "-qO-", "-T", "5",
        "http://notes-api.notes-api.svc.cluster.local/health", timeout=40,
    )
    return res.returncode == 0 and "ok" in res.stdout, (res.stdout + res.stderr).strip()


def test_l_espace_de_noms_impose_le_standard_restricted(cluster) -> None:
    banc, _ = cluster
    privilegie = banc.kubectl(
        "-n", "notes-api", "run", "privilegie", f"--image={CLIENT}", "--restart=Never", "--dry-run=server",
        "--overrides", '{"spec":{"containers":[{"name":"privilegie","image":"' + CLIENT + '",'
        '"securityContext":{"privileged":true}}]}}',
        "-o", "name", timeout=60,
    )
    assert privilegie.returncode != 0 and "restricted" in privilegie.stderr, (
        "Un Pod privilégié est admis dans notes-api : l'espace de noms n'impose pas le standard "
        "restricted des Pod Security Standards (label pod-security.kubernetes.io/enforce).\n  "
        + (privilegie.stdout + privilegie.stderr)[-400:]
    )


def test_notes_api_tourne_sous_le_standard_restricted(cluster) -> None:
    banc, deploiement = cluster
    if deploiement.returncode != 0:
        evenements = banc.kubectl("-n", "notes-api", "get", "events", "--sort-by=.lastTimestamp").stdout
        pytest.fail(
            "Le Deployment notes-api ne devient pas disponible. Sous le standard restricted, "
            "un Pod sans securityContext complet est refusé à la création ; ses ReplicaSets le "
            "disent dans les événements :\n" + evenements[-1500:]
        )
    # Ce que le noyau applique réellement au processus, pas ce que le manifeste
    # déclare : l'uid, l'interdiction d'escalade (NoNewPrivs) et l'ensemble des
    # capacités qu'il pourrait encore acquérir (CapBnd).
    statut = banc.kubectl("-n", "notes-api", "exec", "deploy/notes-api", "--", "cat", "/proc/self/status", timeout=40)
    champs = dict(
        (cle.strip(), valeur.strip())
        for cle, _, valeur in (ligne.partition(":") for ligne in statut.stdout.splitlines())
    )
    uid = champs.get("Uid", "0").split()[0]
    assert uid != "0", f"notes-api tourne sous l'uid {uid} : il doit tourner sans privilège."
    assert champs.get("NoNewPrivs") == "1", (
        "Le processus de notes-api peut encore gagner des privilèges (NoNewPrivs à "
        f"{champs.get('NoNewPrivs')}) : allowPrivilegeEscalation: false."
    )
    assert int(champs.get("CapBnd", "1"), 16) == 0, (
        f"Le processus de notes-api garde des capacités Linux (CapBnd {champs.get('CapBnd')}) : "
        "capabilities: drop: [ALL]."
    )


def test_seul_le_controleur_d_entree_joint_l_api(cluster) -> None:
    banc, deploiement = cluster
    if deploiement.returncode != 0:
        pytest.fail("notes-api n'est pas disponible : le trafic ne peut pas être mesuré.")
    joint, sortie = _joindre_l_api(banc, "ingress")
    assert joint, (
        "Depuis l'espace de noms ingress, notes-api ne répond pas sur /health : le contrôleur "
        f"d'entrée doit pouvoir la joindre sur son port.\n  {sortie[-300:]}"
    )
    joint, _ = _joindre_l_api(banc, "default")
    assert not joint, (
        "Un Pod de l'espace de noms default joint notes-api : seule l'entrée venue de ingress "
        "doit passer, tout le reste est refusé."
    )


def test_notes_api_ne_sort_que_vers_le_dns(cluster) -> None:
    banc, deploiement = cluster
    if deploiement.returncode != 0:
        pytest.fail("notes-api n'est pas disponible : sa sortie ne peut pas être mesurée.")
    res = banc.kubectl("-n", "notes-api", "exec", "deploy/notes-api", "--", "python", "-c", SONDE_SORTIE, timeout=60)
    sortie = (res.stdout + res.stderr).strip()
    assert "DNS-KO" not in sortie, (
        "Depuis notes-api, la résolution DNS échoue : la sortie vers le DNS du cluster "
        f"(kube-dns, port 53 en UDP et TCP) doit rester ouverte.\n  {sortie[-300:]}"
    )
    assert "SORTIE-FERMEE" in sortie, (
        "Depuis notes-api, un serveur de l'espace de noms default répond : un attaquant qui "
        "prend la main sur l'application rebondirait vers le reste du cluster.\n  " + sortie[-300:]
    )


def test_le_pod_ne_porte_pas_de_jeton_et_le_modele_a_jour(cluster, projet: Path) -> None:
    banc, deploiement = cluster
    if deploiement.returncode != 0:
        pytest.fail("notes-api n'est pas disponible : son Pod ne peut pas être inspecté.")
    jeton = banc.kubectl(
        "-n", "notes-api", "exec", "deploy/notes-api", "--", "python", "-c",
        "import os; print(os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount/token'))",
        timeout=40,
    )
    assert jeton.stdout.strip() == "False", (
        "Le Pod de notes-api monte un jeton de l'API Kubernetes, dont l'application ne se sert "
        "pas : volé, il ouvre l'API du cluster. automountServiceAccountToken: false."
    )
    modele = yaml.safe_load((projet / "threat-model.yml").read_text(encoding="utf-8"))
    visees = [m for m in modele.get("threats", []) if str(m.get("id")) == "T-16"]
    assert visees and visees[0].get("status") == "mitigated", (
        "La menace T-16 sur le Pod de notes-api passe à `mitigated`."
    )
    assert (projet / str(visees[0].get("evidence") or "")).is_file(), (
        "La preuve de T-16 doit être un fichier du projet : un manifeste de deploy/k8s/."
    )
