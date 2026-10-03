# V8 : l'admission signée

Neuvième version du **fil rouge** de la formation DevSecOps. Le cluster où
tourne notes-api n'admet plus que les images du registre interne signées par
la plateforme : une image non signée, signée par une autre clé ou venue d'un
autre registre est refusée à la porte.

| | |
|---|---|
| Cible | votre poste : Docker, kind, kubectl, helm et cosign (`mise install`) |
| Durée | environ 50 minutes |
| Leçon jumelée | [Vérifier les artefacts à l'admission](https://blog.stephane-robert.info/docs/conteneurs/orchestrateurs/kubernetes/securiser/supply-chain-security/) |
| Précédent | `capstone-v07-sbom-et-provenance` |
| Suivant | `capstone-v09-runtime-cloisonne` |

```bash
mise install
dsoxlab run   capstone-v08-admission-signee
cd labs/capstone/v08-admission-signee/challenge/work
dsoxlab check capstone-v08-admission-signee
```

Les tests montent un cluster kind avec le registre interne et Kyverno, y
appliquent vos politiques, puis demandent l'admission de Pods et d'un
Deployment, sans rien créer. Le cluster est détruit à la fin.
