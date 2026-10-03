"""Check that the SBOM of the image tells the same story as uv.lock.

    python3 scripts/check_sbom.py sbom.cdx.json uv.lock

The SBOM is a CycloneDX JSON document, produced from the built image (for
instance by `trivy image --format cyclonedx`). Only the Python packages
installed in the application environment are compared: their path starts
with APP_PREFIX. The interpreter's own tools (pip in the base image) are not
the application's dependencies.

Three problems are reported, one line each:

- a package ships in the image but is not in uv.lock: something was installed
  outside the lock, and nobody reviewed it;
- a package ships with another version than the locked one;
- a direct runtime dependency of the project is missing from the image.

Exit code 0 when the SBOM matches the lock, 1 when it does not.
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

APP_PREFIX = "app/.venv/"
FILE_PATH = "aquasecurity:trivy:FilePath"


def normalise(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def shipped(sbom: dict) -> dict[str, str]:
    packages: dict[str, str] = {}
    for component in sbom.get("components", []):
        if not str(component.get("purl", "")).startswith("pkg:pypi/"):
            continue
        props = {p.get("name"): p.get("value") for p in component.get("properties", [])}
        if str(props.get(FILE_PATH, "")).lstrip("/").startswith(APP_PREFIX):
            packages[normalise(component["name"])] = str(component.get("version"))
    return packages


def locked(lock: dict) -> tuple[dict[str, str], set[str]]:
    versions: dict[str, str] = {}
    direct: set[str] = set()
    for package in lock.get("package", []):
        source = package.get("source", {})
        if "virtual" in source or "editable" in source:
            direct = {normalise(d["name"]) for d in package.get("dependencies", [])}
            continue
        versions[normalise(package["name"])] = str(package.get("version"))
    return versions, direct


def problems(sbom_path: Path, lock_path: Path) -> tuple[list[str], int]:
    try:
        sbom = json.loads(sbom_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"{sbom_path}: unreadable CycloneDX document ({exc})"], 0
    lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    in_image = shipped(sbom)
    versions, direct = locked(lock)
    found: list[str] = []
    if not in_image:
        found.append(f"no Python package under {APP_PREFIX} in {sbom_path}: is it the SBOM of the image?")
    for name, version in sorted(in_image.items()):
        if name not in versions:
            found.append(f"{name} {version} ships in the image but is not in uv.lock")
        elif versions[name] != version:
            found.append(f"{name} ships as {version}, uv.lock says {versions[name]}")
    for name in sorted(direct - set(in_image)):
        found.append(f"{name} is a runtime dependency but is missing from the image")
    return found, len(in_image)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    found, count = problems(Path(sys.argv[1]), Path(sys.argv[2]))
    if found:
        for line in found:
            print(f"SBOM: {line}")
        print(f"FAILED: the SBOM and uv.lock disagree on {len(found)} point(s)")
        return 1
    print(f"SBOM matches uv.lock: {count} packages in the application environment")
    return 0


if __name__ == "__main__":
    sys.exit(main())
