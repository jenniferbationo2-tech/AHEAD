"""
Vérifie le catalogue de référence et montre où on en est.

Pour chaque dossier ref_XXX : annonce.txt présent et rempli, fiche.yaml conforme
au format de ahead/schema.py. Puis compte la variété des cas.

Lancer depuis le dossier ahead-ia :
    .venv\\Scripts\\python.exe -m outils.verifier_reference
"""
from collections import Counter
from pathlib import Path

import yaml
from pydantic import ValidationError

from ahead.schema import FicheReference, Metadonnees

DOSSIER = Path(__file__).resolve().parent.parent / "donnees" / "reference"
TEXTE_MODELE = "Collez ici le texte de l'annonce"
CHAMPS = ["nom", "date_debut", "date_fin", "lieu", "format", "organisateur", "prix"]


def charger(dossier):
    """Renvoie (metadonnees, fiche) ou lève une erreur lisible."""
    annonce = dossier / "annonce.txt"
    if not annonce.exists():
        raise ValueError("annonce.txt manquant")
    texte = annonce.read_text(encoding="utf-8").strip()
    if not texte or texte.startswith(TEXTE_MODELE):
        raise ValueError("annonce.txt n'est pas rempli")

    donnees = yaml.safe_load((dossier / "fiche.yaml").read_text(encoding="utf-8"))
    fiche = FicheReference(**donnees.pop("fiche"))
    donnees.pop("notes", None)
    return Metadonnees(**donnees), fiche


def type_de_prix(prix):
    if prix is None:
        return "non indiqué"
    return "gratuit" if "gratuit" in prix.lower() or "free" in prix.lower() else "payant"


def main():
    dossiers = sorted(d for d in DOSSIER.iterdir() if d.is_dir() and not d.name.startswith("_"))
    fiches, erreurs = [], 0
    for dossier in dossiers:
        try:
            fiches.append(charger(dossier))
        except FileNotFoundError:
            erreurs += 1
            print(f"  {dossier.name} : fiche.yaml manquant")
        except ValidationError as e:
            erreurs += 1
            print(f"  {dossier.name} :")
            for err in e.errors():
                champ = ".".join(str(x) for x in err["loc"]) or "fiche"
                print(f"      - {champ} : {err['msg']}")
        except (ValueError, yaml.YAMLError, AttributeError) as e:
            erreurs += 1
            print(f"  {dossier.name} : {e}")

    print(f"\n{len(fiches)} fiche(s) valide(s), {erreurs} en erreur, objectif 30.\n")
    if not fiches:
        return

    evenements = [(m, f) for m, f in fiches if f.est_un_evenement]
    pieges = len(fiches) - len(evenements) + sum(
        1 for m, f in evenements if f.date_debut and f.date_debut < m.date_collecte)
    incompletes = sum(1 for _, f in evenements if any(getattr(f, c) is None for c in CHAMPS))
    formats = Counter(f.format or "non indiqué" for _, f in evenements)
    prix = Counter(type_de_prix(f.prix) for _, f in evenements)
    langues = Counter(m.langue for m, _ in fiches)
    themes = Counter(t for _, f in evenements for t in f.themes)

    print("Variété (objectif entre parenthèses) :")
    lignes = [(nom, formats[nom], "5") for nom in ["en ligne", "présentiel", "hybride"]]
    lignes += [(f"prix {nom}", prix[nom], "5") for nom in ["gratuit", "payant", "non indiqué"]]
    lignes += [("en anglais", langues["en"], "5"), ("incomplètes", incompletes, "5"),
               ("pièges", pieges, "3 ou 4")]
    for nom, nombre, objectif in lignes:
        print(f"  {nom:17}: {nombre:3}  ({objectif})")
    print("  Afrique / ailleurs : à compter à la main (10 / 10)")
    print("\nThèmes : " + ", ".join(f"{t} {n}" for t, n in themes.most_common()))


if __name__ == "__main__":
    main()
