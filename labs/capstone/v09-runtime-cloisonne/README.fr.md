# V9 : l'exécution cloisonnée

Dixième version du **fil rouge** de la formation DevSecOps. notes-api tourne
désormais sous le standard restricted des Pod Security Standards, sans jeton
d'API, et derrière des NetworkPolicies qui ne laissent entrer que le
contrôleur d'entrée et sortir que le DNS.

| | |
|---|---|
| Cible | votre poste : Docker, kind et kubectl (`mise install`) |
| Durée | environ 50 minutes |
| Leçon jumelée | [Cloisonner le réseau avec les NetworkPolicies](https://blog.stephane-robert.info/docs/conteneurs/orchestrateurs/kubernetes/network-policies/) |
| Précédent | `capstone-v08-admission-signee` |
| Suivant | `capstone-v10-vex-et-exceptions` |

```bash
mise install
dsoxlab run   capstone-v09-runtime-cloisonne
cd labs/capstone/v09-runtime-cloisonne/challenge/work
dsoxlab check capstone-v09-runtime-cloisonne
```

Les tests construisent votre image, la déploient sur un cluster kind avec vos
manifestes, puis mesurent le trafic réel. Le cluster est détruit à la fin.
