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
| `subject` | Numéro de matière, de 0 à 5 (météo, mécanique du vol, aéronef, navigation, histoire, anglais). |
| `no_subject` | Numéro de la question dans la matière, commence à 0. |
| `no` | Ordre dans l'examen, commençant à 0. |
| `content_verbatim` | Énoncé original. Généralement ne pas utiliser, si `content_fixed` existe.|
| `content_fixed` | Énoncé corrigé. |
| `choice_[abcd]`| Les quatre propositions de réponse. (`choice_a`) réponse A, etc.) |
| `answer` | Indice de la réponse correcte (0=A, 1=B, 2=C, 3=D). |
| `chapter` | Numéro de chapitre du programme, séparées par virgule si correspond à plusieurs chapitres. /!\ Les chapitres ne correspondent pas au `label`. |
| `attachment_link` | Lien vers l'image d'illustration si existant |
| `mixed_choices` | Indique si l'ordre des choix peut être aléatoire. |


Les indices des chapitres sont :
```
    "1.1 Les aéronefs": 0 
    "1.2 Instrumentation": 1 
    "1.3 Moteurs": 2 
    "2.1 La sustentation de l'aile": 3 
    "2.2 Le vol stabilisé": 4,  
    "2.3 L'aérostation et le vol spatial": 5 
    "3.1 L'atmosphère": 6 
    "3.2  Les masses d'air et les fronts": 7
    "3.3  Les nuages": 8
    "3.4 Les vents": 9 
    "3.5 Les phénomènes dangereux": 10 
    "3.6 L'information météo": 11 
    "4.1 Réglementation": 12 
    "4.2 Sécurité des Vols (SV) et Facteurs Humains (FH)": 13 
    "4.3 Navigation": 14
```

## FIXME

Hlo2EYVT 2017-3-13 et 2024-3-13 Un avion à ailes en flèche est représenté par la figure  Add link
T8XH6hdj subject in exam not matching chapters split for lessons (exam meca fluid, seen as aeronef)
68lntUsI subject in exam not matching chapters split for lessons (exam meca fluid, seen as aeronef)


## TODO

move icons/ to assets/




