#!/usr/bin/env python3
"""Calcule scripts/doc_url_en.json : guide français -> sa traduction anglaise.

Les liens vers les guides ne s'écrivent pas à la main. Un `doc_url` désigne la
leçon française (la CLI dsoxlab le lit) ; la version anglaise, quand elle
existe, se déduit du site lui-même : chaque page anglaise y déclare la page
française qu'elle traduit dans son champ `translationOf`.

Le script lit le dépôt du site, retient les URL du blog citées par ce catalogue
(`doc_url` des labs et liens des fichiers Markdown), et écrit la table des
seules URL qui ont une traduction. Une URL absente de la table n'en a pas : le
README anglais garde alors le guide français, marqué.

    python3 scripts/gen_doc_url_en.py ~/Projets/test-astro-5
    python3 scripts/gen_doc_url_en.py ~/Projets/test-astro-5 --check

Les URL restent sur blog.stephane-robert.info, le domaine de production.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SORTIE = ROOT / "scripts" / "doc_url_en.json"
BLOG = "https://blog.stephane-robert.info"
RE_URL = re.compile(re.escape(BLOG) + r"/docs/[A-Za-z0-9/_.-]*")
RE_TRANSLATION = re.compile(r"^translationOf:\s*['\"]?([^'\"\s]+)", re.MULTILINE)
RE_FRONT = re.compile(r"\A---\n(.*?)\n---", re.DOTALL)


def urls_citees() -> set[str]:
    """Toutes les URL de guides français citées par le catalogue."""
    urls: set[str] = set()
    for fichier in ROOT.rglob("*"):
        if ".git" in fichier.parts or not fichier.is_file() or fichier.suffix not in (".md", ".yaml", ".yml"):
            continue
        if "challenge" in fichier.parts and "work" in fichier.parts:
            continue
        urls.update(RE_URL.findall(fichier.read_text(encoding="utf-8", errors="replace")))
    return {u if u.endswith("/") else u + "/" for u in urls}


def traductions(site: Path) -> dict[str, str]:
    """URL française -> URL anglaise, lue dans le `translationOf` de chaque page anglaise."""
    racine_en = site / "src" / "content" / "docs-en"
    if not racine_en.is_dir():
        sys.exit(f"{racine_en} introuvable : passez le chemin du dépôt du site")
    table: dict[str, str] = {}
    for page in racine_en.rglob("*.md*"):
        tete = RE_FRONT.match(page.read_text(encoding="utf-8", errors="replace"))
        if not tete:
            continue
        m = RE_TRANSLATION.search(tete.group(1))
        if not m or not m.group(1).startswith("docs/"):
            continue
        chemin_en = page.relative_to(racine_en).with_suffix("")
        if chemin_en.name == "index":
            chemin_en = chemin_en.parent
        source = m.group(1).removesuffix("/index")
        table[f"{BLOG}/{source}/"] = f"{BLOG}/en/docs/{chemin_en.as_posix()}/"
    return table


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("site", type=Path, help="chemin du dépôt du site")
    parser.add_argument("--check", action="store_true", help="échoue si la table est périmée")
    args = parser.parse_args()
    table_site = traductions(args.site.expanduser())
    attendu = {u: table_site[u] for u in sorted(urls_citees()) if u in table_site}
    rendu = json.dumps(attendu, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        actuel = SORTIE.read_text(encoding="utf-8") if SORTIE.exists() else ""
        if actuel != rendu:
            print("scripts/doc_url_en.json est périmé : relancez sans --check", file=sys.stderr)
            return 1
        print("table des traductions à jour")
        return 0
    SORTIE.write_text(rendu, encoding="utf-8")
    print(f"{SORTIE.relative_to(ROOT)} : {len(attendu)} guide(s) traduit(s) sur {len(urls_citees())} cité(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
