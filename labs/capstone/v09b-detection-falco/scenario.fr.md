# V9b : voir quand quelqu'un est entré

## Situation

V9 a fermé notes-api : Pod restreint, réseau cloisonné. Ces protections
réduisent ce qu'un attaquant peut faire, mais aucune ne dit **quand** il est
entré. Un shell ouvert dans le conteneur, ou un fichier modifié dans le code
qui tourne, passerait sans un mot.

Sur la machine `falco-1.lab`, une Ubuntu 24.04, notes-api tourne dans Docker
sous le nom `notes-api`, et **Falco 0.45.0** la surveille avec sa sonde eBPF
moderne. Le setup a déjà fait écrire chaque alerte, en JSON, dans
`/var/log/falco/events.json`. Il manque les règles qui disent ce qui ne doit
jamais arriver dans notes-api.

Pratique SSDF visée : RV.1 (identifier et confirmer les vulnérabilités en continu).

## Objectif

Écrire `/etc/falco/rules.d/notes-api.yaml`, chargé par Falco à chaque
démarrage :

1. un **shell** ouvert dans le conteneur notes-api lève une alerte de niveau
   **WARNING** au moins, qui cite le conteneur et la **ligne de commande** ;
2. une **écriture sous /app** dans le conteneur notes-api lève une alerte de
   niveau **ERROR** au moins, qui cite le conteneur et le **fichier** ;
3. l'activité normale de notes-api (son serveur, sa sonde de santé en
   Python) et un shell dans un **autre** conteneur ne lèvent **aucune**
   alerte de vos règles ;
4. les règles passent `falco -V` et **survivent** à un redémarrage de Falco.

## Repères

- `dsoxlab run` vous connecte à `falco-1.lab`. `sudo docker exec notes-api sh`
  ouvre le shell que vos règles doivent voir.
- Les macros `spawned_process` et `open_write` viennent des règles par
  défaut, `/etc/falco/falco_rules.yaml` : valider votre fichier seul échoue,
  validez les deux, `falco -V /etc/falco/falco_rules.yaml -V <votre fichier>`.
- `container.name`, `proc.name`, `proc.cmdline`, `fd.name` et `user.name`
  sont les champs utiles. La sortie d'une règle ne transporte que les champs
  qu'elle cite.
- Le service s'appelle `falco-modern-bpf.service`.

## Vérifier

```bash
dsoxlab check capstone-v09b-detection-falco
```

Cinq contrôles, vingt points chacun. Ils provoquent eux-mêmes un shell et une
écriture dans notes-api, puis ce qui ne doit rien déclencher, et lisent les
alertes de vos seules règles dans `/var/log/falco/events.json`.
