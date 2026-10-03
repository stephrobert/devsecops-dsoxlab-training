# Politique de sécurité

**Langue :** [English](./SECURITY.md) · [Français](./SECURITY.fr.md)

## Versions supportées

`devsecops-dsoxlab-training` est en développement actif. Les correctifs de
sécurité sont appliqués à la dernière version de la branche `main`.

| Version | Supportée |
| --- | --- |
| dernière (`main`) | oui |
| plus anciennes | non |

## Signaler une vulnérabilité

**N'ouvrez pas d'issue publique pour une vulnérabilité de sécurité.**

Si vous pensez avoir trouvé une vulnérabilité, signalez-la en privé :

- De préférence : ouvrez un
  [avis de sécurité privé](https://github.com/stephrobert/devsecops-dsoxlab-training/security/advisories/new)
  sur GitHub.
- Sinon, utilisez les coordonnées publiées sur
  <https://blog.stephane-robert.info>.

Merci d'inclure :

- une description de la vulnérabilité et de son impact,
- les étapes pour la reproduire (commande, environnement, `act --version`,
  `dsoxlab --version`),
- tout journal ou preuve de concept pertinent.

Nous vous tiendrons informé de l'avancement du correctif et vous créditerons
dans les notes de version si vous le souhaitez.

## Politique de divulgation

Nous pratiquons la divulgation coordonnée et nous engageons sur les délais
suivants, décomptés à partir de la réception de votre signalement :

| Étape | Délai visé |
| --- | --- |
| Accusé de réception de votre signalement | sous **48 heures** |
| Évaluation initiale et qualification de la sévérité | sous **5 jours** |
| Correctif publié, ou plan de remédiation écrit | sous **30 jours** |
| Divulgation publique de la vulnérabilité | sous **90 jours** |

Nous publions l'avis de sécurité dès qu'un correctif est disponible, ou au plus
tard à l'échéance des **90 jours**, selon ce qui arrive en premier. Si une
vulnérabilité est activement exploitée, nous pouvons la divulguer plus tôt pour
protéger les utilisateurs. Si un correctif complexe demande plus de temps, nous
vous prévenons avant l'échéance et convenons d'une nouvelle date avec vous,
plutôt que de la laisser expirer sans rien dire.

## Périmètre

Ce dépôt livre du **contenu de labs** : le projet `notes-api` à chaque étape du
fil rouge, des fixtures, des tests pytest qui jouent des workflows GitHub
Actions avec act, et des solutions de référence chiffrées, exécutés par la CLI
externe `dsoxlab` sur la machine de l'apprenant.

`notes-api` est **volontairement vulnérable** : une requête SQL concaténée, une
dépendance vulnérable épinglée, un Dockerfile qui tourne en root, un Terraform
trop ouvert. Ces défauts sont le sujet des labs, qui les font corriger version
après version. Ils ne sont pas des vulnérabilités du dépôt, et ne se signalent
pas ici.

Sont dans le périmètre :

- du matériel de lab dangereux ou malveillant, notamment un workflow qui
  contacterait une destination non déclarée ou exfiltrerait des données du
  poste de l'apprenant ;
- une fuite de secret réel, une clé privée ou un jeton d'API commité par
  erreur ;
- une solution de référence livrée en clair, qui gâche le lab et reste dans
  l'historique ;
- une action ou une image référencée sans épinglage par SHA ou par digest dans
  ce que le dépôt livre comme référence.

Ne sont pas dans le périmètre :

- les vulnérabilités du moteur `dsoxlab` lui-même, qui relèvent de
  [son propre dépôt](https://github.com/stephrobert/dsoxlab) ;
- celles d'act, de l'image du runner, des actions GitHub ou de toute dépendance
  tierce, à signaler à leurs projets respectifs ;
- les défauts volontaires de `notes-api` décrits ci-dessus ;
- un lab qui échoue ou qui note mal : c'est un défaut, il s'ouvre en issue
  publique.

## Ce que ce dépôt ne vous demandera jamais

Aucun lab n'exige de fournir un secret réel. Les secrets que les tests injectent
pour voir un pipeline échouer sont **factices**, écrits dans une copie
temporaire du projet et détruits avec elle.
