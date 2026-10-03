# V11 : mesurer la fiabilité

Douzième et dernière version du **fil rouge** de la formation DevSecOps.
notes-api reçoit un SLO de disponibilité, une alerte qui réveille l'astreinte
quand le budget d'erreurs brûle trop vite, le runbook vers lequel l'alerte
renvoie, et le calcul des quatre métriques DORA depuis ses journaux.

| | |
|---|---|
| Cible | votre poste : uv, Python et act (`mise install`), **Docker** qui répond |
| Durée | environ 60 minutes |
| Leçon jumelée | [SLO, SLI et error budgets](https://blog.stephane-robert.info/docs/devops/fondamentaux/slo-sli-error-budget/) |
| Précédent | `capstone-v10-vex-et-exceptions` |

```bash
mise install
dsoxlab run   capstone-v11-slo-et-dora
cd labs/capstone/v11-slo-et-dora/challenge/work
act pull_request
dsoxlab check capstone-v11-slo-et-dora
```

Les tests soumettent votre alerte à des séries de requêtes connues avec
promtool, et votre script DORA à des journaux dont ils connaissent les
réponses.
