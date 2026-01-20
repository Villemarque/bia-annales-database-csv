# Annales du BIA, format CSV/TSV

Toutes les questions des différents examen du BIA depuis la réforme du BIA en 2015 ! Ainsi qu'un site intéractif et fonctionnant hors-ligne (TODO) pour s'entrainer.

## Organisation

Le fichier `annales-bia.csv` contient les annales du BIA au format TSV (séparateur tabulation).

Le code-source du site de QCM se trouve dans `site`. Voir 

### Description des champs

| Champ | Description |
| :--- | :--- |
| `qid` | Identifiant unique. |
| `year` | Année de l'examen. |
| `subject` | Numéro de matière, de 0 à 6 (météo, mécanique du vol, aéronef, navigation, histoire, anglais). |
| `no_subject` | Numéro de la question dans la matière, commence à 0. |
| `no` | Ordre dans l'examen, commençant à 0. |
| `content_verbatim` | Énoncé original. Généralement ne pas utiliser, si `content_fixed` existe.|
| `content_fixed` | Énoncé corrigé. |
| `choice_[abcd]`| Les quatre propositions de réponse. (`choice_a`) réponse A, etc.) |
| `answer` | Indice de la réponse correcte (0=A, 1=B, 2=C, 3=D). |
| `chapter` | Référence au chapitre du programme. /!\ Les chapitres ne correspondent pas au `label`. |
| `attachment_link` | Lien vers l'image d'illustration si existant |
| `mixed_choices` | Indique si l'ordre des choix peut être aléatoire. |
