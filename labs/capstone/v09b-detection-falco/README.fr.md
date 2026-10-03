# V9b : la détection à l'exécution

Version annexe du **fil rouge** de la formation DevSecOps, entre V9 et V10.
Sur une vraie machine, notes-api tourne sous Falco, et ses règles signalent un
shell ouvert dans son conteneur ou une écriture dans son code, sans alerter
sur son activité normale.

| | |
|---|---|
| Cible | une VM Ubuntu 24.04 provisionnée par dsoxlab (KVM ou Incus) |
| Durée | environ 50 minutes |
| Leçon jumelée | [Détection runtime avec Falco](https://blog.stephane-robert.info/docs/conteneurs/orchestrateurs/kubernetes/securiser/falco/) |
| Précédent | `capstone-v09-runtime-cloisonne` |
| Suivant | `capstone-v10-vex-et-exceptions` |

```bash
dsoxlab instructor bootstrap
dsoxlab use --provider kvm
dsoxlab provision
dsoxlab run   capstone-v09b-detection-falco
dsoxlab check capstone-v09b-detection-falco
```

Falco lit les appels système du noyau : il lui faut une vraie machine, et un
cluster kind, qui partage le noyau de l'hôte, ne prouverait rien de plus. Les
tests provoquent eux-mêmes les actions à détecter, et lisent les alertes en
JSON.
