# V9 : si notes-api tombe, elle tombe seule

## Situation

Le cluster n'admet plus que des images signées (V8). Reste ce qui se passe
**une fois l'image démarrée**. Les manifestes de `deploy/k8s/` ont été écrits
avec les réglages par défaut : le processus de notes-api peut gagner des
privilèges, garde ses capacités Linux, monte un jeton de l'API Kubernetes dont
il ne se sert pas, et son Pod joint n'importe quel autre Pod du cluster. Une
seule faille dans l'application ouvre donc tout le cluster. Le modèle de
menace la nomme : T-16, `open`.

Le contrôleur d'entrée tourne dans l'espace de noms `ingress` : c'est lui, et
lui seul, qui doit joindre notes-api.

Le répertoire `challenge/work` contient le projet tel que V8 l'a laissé, avec
ces manifestes.

Pratique SSDF visée : PW.9 (configurer le logiciel sûr par défaut).

## Objectif

1. L'espace de noms `notes-api` **impose** le standard **restricted** des Pod
   Security Standards : un Pod privilégié y est refusé à l'admission.
2. Le Deployment passe ce standard et devient disponible : processus sans
   privilège, **escalade interdite**, **toutes les capacités retirées**,
   profil seccomp par défaut, et **aucun jeton d'API** monté.
3. Des **NetworkPolicies** ne laissent entrer que le trafic venu de
   l'espace de noms `ingress`, sur le port de l'API, et ne laissent sortir
   que les requêtes DNS vers kube-dns.
4. La menace T-16 passe à `mitigated`, avec sa preuve.

## Repères

- Le standard s'impose par un label de l'espace de noms :
  `pod-security.kubernetes.io/enforce: restricted`. Un Deployment qui ne le
  respecte pas est créé, mais ses Pods sont refusés : les événements du
  ReplicaSet le disent.
- Une NetworkPolicy isole les Pods qu'elle sélectionne, dans le sens qu'elle
  déclare (`policyTypes`) : tout ce qu'elle n'autorise pas est refusé.
- Un Pod qui ne résout plus aucun nom a perdu sa sortie DNS : kube-dns vit
  dans `kube-system`, avec le label `k8s-app: kube-dns`, en UDP et en TCP.
- Ce lab ne couvre pas la détection à l'exécution (Falco) : elle exige une
  vraie machine, pas un cluster dans Docker.

## Vérifier

```bash
dsoxlab check capstone-v09-runtime-cloisonne
```

Cinq contrôles, vingt points chacun. Ils montent un cluster kind, construisent
votre image, appliquent vos manifestes, puis mesurent le trafic réel depuis
l'espace de noms `ingress`, depuis `default`, et depuis notes-api elle-même.
Comptez trois à quatre minutes.
