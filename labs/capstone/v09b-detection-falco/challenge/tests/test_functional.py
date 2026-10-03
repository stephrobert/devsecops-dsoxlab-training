"""V9b, la détection à l'exécution : cinq contrôles, vingt points chacun.

## Ce que ces tests font

Ils se connectent en SSH à falco-1.lab, où notes-api tourne dans Docker sous
Falco 0.45.0, et provoquent eux-mêmes ce que les règles doivent voir : un
shell ouvert dans le conteneur notes-api, une écriture sous /app. Ils lisent
ensuite les alertes que Falco écrit en JSON dans /var/log/falco/events.json,
et n'en retiennent que celles des règles de l'apprenant, lues dans
/etc/falco/rules.d/notes-api.yaml.

Chaque action provoquée porte un MARQUEUR unique, et les tests le cherchent
dans le texte de l'alerte : la règle doit citer la ligne de commande (ou le
fichier, pour l'écriture). Mesuré le 2026-10-03 sur Falco 0.45.0 :
`output_fields` ne contient que les champs que la sortie de la règle cite.

Ils provoquent aussi ce qui ne doit RIEN déclencher : l'activité normale de
l'application, et un shell dans un autre conteneur. Une règle qui alerte sur
tout ne détecte rien : on finit par ne plus la lire.
"""

from __future__ import annotations

import json
import secrets
import time

import pytest
import yaml

from conftest import lab_host

HOTE = "falco-1.lab"
REGLES = "/etc/falco/rules.d/notes-api.yaml"
JOURNAL = "/var/log/falco/events.json"
SERVICE = "falco-modern-bpf.service"
REGLES_PAR_DEFAUT = "/etc/falco/falco_rules.yaml"
NIVEAUX = ["debug", "informational", "notice", "warning", "error", "critical", "alert", "emergency"]
ATTENTE = 20


@pytest.fixture(scope="module")
def hote():
    return lab_host(HOTE)


def _regles(hote) -> set[str]:
    fichier = hote.file(REGLES)
    assert fichier.exists, f"{REGLES} est introuvable : notes-api n'a aucune règle Falco."
    contenu = yaml.safe_load(fichier.content_string) or []
    noms = {e["rule"] for e in contenu if isinstance(e, dict) and "rule" in e}
    assert noms, f"{REGLES} ne déclare aucune règle (élément `rule:`)."
    return noms


def _taille(hote) -> int:
    return int(hote.check_output(f"stat -c %s {JOURNAL}"))


def _alertes(hote, depuis: int, regles: set[str]) -> list[dict]:
    """Les alertes des règles de l'apprenant écrites après l'octet `depuis`."""
    brut = hote.check_output(f"tail -c +{depuis + 1} {JOURNAL}")
    alertes = []
    for ligne in brut.splitlines():
        try:
            evenement = json.loads(ligne)
        except ValueError:
            continue
        if evenement.get("rule") in regles:
            alertes.append(evenement)
    return alertes


def _attendre(hote, depuis: int, regles: set[str], critere) -> list[dict]:
    fin = time.monotonic() + ATTENTE
    while time.monotonic() < fin:
        trouvees = [a for a in _alertes(hote, depuis, regles) if critere(a)]
        if trouvees:
            return trouvees
        time.sleep(1)
    return []


def _niveau(alerte: dict) -> int:
    return NIVEAUX.index(str(alerte.get("priority", "debug")).lower())


def _champ(alerte: dict, cle: str) -> str:
    return str((alerte.get("output_fields") or {}).get(cle, ""))


def _marqueur() -> str:
    return f"fil-rouge-{secrets.token_hex(4)}"


def _cite(alerte: dict, *mots: str) -> bool:
    texte = str(alerte.get("output", ""))
    return all(m in texte for m in mots)


def _provoquer_un_shell(hote) -> str:
    marqueur = _marqueur()
    hote.run(f"docker exec notes-api sh -c 'echo {marqueur} > /dev/null'")
    return marqueur


def test_les_regles_sont_valides_et_falco_tourne(hote) -> None:
    _regles(hote)
    # Les macros communes (spawned_process, open_write...) vivent dans les
    # règles par défaut : la validation charge les deux fichiers.
    validation = hote.run(f"falco -V {REGLES_PAR_DEFAUT} -V {REGLES}")
    assert validation.rc == 0, (
        f"Falco refuse {REGLES} :\n{(validation.stdout + validation.stderr)[-800:]}"
    )
    assert hote.service(SERVICE).is_running, (
        f"{SERVICE} ne tourne plus : des règles chargées par un Falco arrêté ne détectent rien."
    )
    assert hote.run("docker inspect -f '{{.State.Running}}' notes-api").stdout.strip() == "true", (
        "Le conteneur notes-api ne tourne plus."
    )


def test_un_shell_dans_notes_api_declenche_une_alerte(hote) -> None:
    regles = _regles(hote)
    depuis = _taille(hote)
    marqueur = _provoquer_un_shell(hote)
    alertes = _attendre(hote, depuis, regles, lambda a: _cite(a, "notes-api", marqueur))
    assert alertes, (
        "Un shell ouvert dans le conteneur notes-api (docker exec notes-api sh) ne déclenche "
        f"aucune alerte de vos règles en {ATTENTE} s, ou l'alerte ne cite ni le conteneur ni "
        "la ligne de commande."
    )
    assert max(_niveau(a) for a in alertes) >= NIVEAUX.index("warning"), (
        "Le shell est détecté, mais sous le niveau WARNING : une intrusion dans le conteneur "
        "ne se range pas avec les informations."
    )


def test_une_ecriture_dans_le_code_declenche_une_alerte(hote) -> None:
    regles = _regles(hote)
    depuis = _taille(hote)
    marqueur = _marqueur()
    hote.run(f"docker exec -u 0 notes-api touch /app/src/{marqueur}.py")
    hote.run(f"docker exec -u 0 notes-api rm -f /app/src/{marqueur}.py")
    alertes = _attendre(hote, depuis, regles, lambda a: _cite(a, "notes-api", f"/app/src/{marqueur}.py"))
    assert alertes, (
        "Un fichier créé sous /app/src dans notes-api ne déclenche aucune alerte de vos règles "
        f"en {ATTENTE} s, ou l'alerte ne cite pas le fichier : le code qui tourne peut changer "
        "en silence."
    )
    assert max(_niveau(a) for a in alertes) >= NIVEAUX.index("error"), (
        "L'écriture dans le code est détectée, mais sous le niveau ERROR : modifier le code en "
        "production est plus grave qu'un shell ouvert."
    )


def test_l_activite_normale_ne_declenche_rien(hote) -> None:
    regles = _regles(hote)
    depuis = _taille(hote)
    hote.run("docker exec notes-api python -c \"import urllib.request; "
             "urllib.request.urlopen('http://127.0.0.1:5000/health')\"")
    hote.run("docker run --rm --entrypoint sh notes-api:v9 -c 'id'")
    time.sleep(8)
    bruit = _alertes(hote, depuis, regles)
    assert not bruit, (
        "Vos règles alertent sur ce qui est normal, ou hors de notes-api : "
        + "; ".join(f"{a.get('rule')} ({_champ(a, 'container.name')}, {_champ(a, 'proc.cmdline')})" for a in bruit[:3])
        + ". Une règle qui alerte sur tout finit par ne plus être lue."
    )


def test_les_regles_survivent_a_un_redemarrage(hote) -> None:
    regles = _regles(hote)
    hote.run(f"systemctl restart {SERVICE}")
    fin = time.monotonic() + 60
    while time.monotonic() < fin and not hote.service(SERVICE).is_running:
        time.sleep(2)
    time.sleep(5)
    depuis = _taille(hote)
    marqueur = _provoquer_un_shell(hote)
    alertes = _attendre(hote, depuis, regles, lambda a: _cite(a, "notes-api", marqueur))
    assert alertes, (
        f"Après un redémarrage de {SERVICE}, le shell dans notes-api n'est plus détecté : les "
        "règles doivent vivre dans /etc/falco/rules.d/, pas dans une commande lancée à la main."
    )
