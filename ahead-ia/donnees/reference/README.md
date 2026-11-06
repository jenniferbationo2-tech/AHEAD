# Catalogue de référence

30 vraies annonces d'événements tech, chacune avec la fiche corrigée à la main.
Ce catalogue sert trois fois :

1. **Base de l'assistant V1** : il répond à partir de ces fiches.
2. **Jeu de test de l'extraction** : on compare la fiche produite par l'IA à la fiche corrigée.
3. **Banc d'essai des fournisseurs** : Gemini, Claude et Mistral passent le même test.

## Ajouter une annonce

1. Copier le dossier `_modele` et le renommer `ref_001`, `ref_002`...
2. Dans `annonce.txt` : coller le texte de l'annonce **tel quel**, même mal écrit.
3. Dans `fiche.yaml` : remplir les champs **à partir du texte seulement**.
4. Vérifier : depuis le dossier `ahead-ia`, lancer
   `.venv\Scripts\python.exe -m outils.verifier_reference`

## Règles de remplissage

- Une information absente du texte reste `null`, même si on la connaît par ailleurs.
  On mesure ce que l'IA peut tirer du texte, pas ce qu'on sait.
- Prix absent : `null`, jamais « gratuit » par défaut.
- Année absente du texte : on la déduit de `date_collecte` (prochaine occurrence) et on le note dans `notes`.
- En cas de doute, choisir, puis l'écrire dans `notes`.

## Thèmes autorisés

Intelligence artificielle · Développement logiciel · Données · Cybersécurité · Robotique ·
Agriculture · Santé numérique · Entrepreneuriat · Financement · Autre

## Viser la variété (sur 30 annonces)

| Cas | Objectif |
|---|---|
| En Afrique / ailleurs | au moins 10 / 10 |
| En ligne, présentiel, hybride | au moins 5 de chaque |
| Gratuit / payant / prix non indiqué | au moins 5 de chaque |
| En anglais | au moins 5 |
| Annonce incomplète (pas de date de fin, pas de lieu...) | au moins 5 |
| Piège : pas un événement, ou événement déjà passé | 3 ou 4 |

Le script de vérification affiche où vous en êtes sur ces objectifs (sauf Afrique / ailleurs, à compter à la main).

## Où trouver des annonces

Sites d'incubateurs et de communautés tech, universités, Eventbrite, Meetup, pages
d'événements LinkedIn, newsletters tech, sites d'organisateurs (GITEX Africa, VivaTech,
AI Summit...). Toujours garder l'adresse de la page dans `source_url`.
