# V7 : SBOM et provenance

Huitième version du **fil rouge** de la formation DevSecOps. Le pipeline de
notes-api produit l'inventaire de ce que l'image embarque et le confronte au
verrou. Le job de déploiement atteste la provenance de chaque archive, et un
script refuse d'en déployer une que le pipeline de main n'a pas construite.

| | |
|---|---|
| Cible | votre poste : uv, Python et act (`mise install`), **Docker** qui répond |
| Durée | environ 55 minutes |
| Leçon jumelée | [De la provenance SLSA à la décision](https://blog.stephane-robert.info/docs/securiser/supply-chain/attestations/slsa-provenance-decision/) |
| Précédent | `capstone-v06-image-et-iac` |

```bash
mise install
dsoxlab run   capstone-v07-sbom-et-provenance
cd labs/capstone/v07-sbom-et-provenance/challenge/work
act pull_request
dsoxlab check capstone-v07-sbom-et-provenance
```

Les tests jouent votre pipeline sur une pull request, puis sur une copie dont
l'image installe un paquet hors du verrou. Ils exécutent aussi votre script
de vérification avec un faux `gh`, pour lire ce qu'il exige.
