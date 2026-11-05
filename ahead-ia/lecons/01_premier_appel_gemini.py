"""
Leçon 1 : comment fonctionne un LLM (version Gemini, clé gratuite).

Mêmes quatre expériences que 01_premier_appel.py (version Claude) :
  1. Les tokens : ce que le modèle lit vraiment.
  2. Un premier appel, avec ses tokens.
  3. Pas de mémoire : chaque appel repart de zéro.
  4. L'hallucination, et comment le contexte la corrige (l'idée du RAG).

Lancer depuis le dossier ahead-ia :
    .venv\\Scripts\\python.exe lecons\\01_premier_appel_gemini.py
"""
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Alias qui pointe toujours vers le modèle Flash courant, disponible en offre gratuite.
MODELE = "gemini-flash-latest"


def message(role, texte):
    """Un tour de conversation. Chez Gemini, le rôle du modèle s'appelle « model »."""
    return types.Content(role=role, parts=[types.Part(text=texte)])


def appeler(client, contenus, system=None, reflexion="low"):
    """Envoie une conversation au modèle. Renvoie le texte et l'usage en tokens."""
    config = types.GenerateContentConfig(
        system_instruction=system,
        # reflexion : combien le modèle réfléchit avant de répondre (low, medium, high).
        thinking_config=types.ThinkingConfig(thinking_level=reflexion),
    )
    # Le service gratuit est parfois surchargé (erreur 503) : on réessaie après une pause
    # qui double à chaque échec (5 s, 10 s, 20 s). C'est le « backoff exponentiel ».
    for tentative in range(4):
        try:
            reponse = client.models.generate_content(model=MODELE, contents=contenus, config=config)
            break
        except errors.ServerError:
            if tentative == 3:
                raise
            pause = 5 * 2 ** tentative
            print(f"   (serveur surchargé, nouvel essai dans {pause} s)")
            time.sleep(pause)
    # Si la réponse est bloquée par les filtres de sécurité, il n'y a pas de texte.
    texte = reponse.text or "[pas de texte : réponse bloquée ou vide]"
    return texte, reponse.usage_metadata


def afficher_usage(usage):
    reflexion = usage.thoughts_token_count or 0
    print(f"   -> {usage.prompt_token_count} tokens envoyés,"
          f" {usage.candidates_token_count} tokens de réponse,"
          f" {reflexion} tokens de réflexion")


def titre(texte):
    print("\n" + "=" * 70 + f"\n{texte}\n" + "=" * 70)


def experience_1_tokens(client):
    titre("1. LES TOKENS")
    phrases = {
        "français": "Le Forum international de l'intelligence artificielle se tiendra"
                    " à Ouagadougou du 12 au 14 mars 2027.",
        "anglais": "The International Artificial Intelligence Forum will take place"
                   " in Ouagadougou from March 12 to 14, 2027.",
    }
    for langue, phrase in phrases.items():
        compte = client.models.count_tokens(model=MODELE, contents=phrase)
        print(f"{langue:9} : {len(phrase)} caractères -> {compte.total_tokens} tokens")
    print("\nÀ retenir : le modèle ne lit pas des lettres mais des morceaux de mots."
          "\nOn paie au token, et la même idée ne coûte pas pareil selon la langue.")


def experience_2_premier_appel(client):
    titre("2. UN PREMIER APPEL")
    question = "En deux phrases, qu'est-ce qu'un salon professionnel ?"
    print(f"Question : {question}\n")
    texte, usage = appeler(client, [message("user", question)])
    print(texte)
    afficher_usage(usage)
    print("\nÀ retenir : en offre payante, les tokens produits coûtent bien plus cher que"
          "\nles tokens envoyés, et la réflexion interne compte comme des tokens produits.")


def experience_3_sans_memoire(client):
    titre("3. PAS DE MÉMOIRE")
    presentation = message("user", "Je m'appelle Jennifer et je travaille sur AHEAD.")
    question = message("user", "Comment je m'appelle ? Réponds en une phrase.")

    texte, _ = appeler(client, [presentation])
    print(f"Appel 1 (présentation) : {texte}\n")

    texte, _ = appeler(client, [question])
    print(f"Appel 2 (question seule) : {texte}\n")

    historique = [presentation, message("model", "Enchantée, Jennifer !"), question]
    texte, _ = appeler(client, historique)
    print(f"Appel 3 (question + historique renvoyé) : {texte}")
    print("\nÀ retenir : le modèle ne garde rien entre deux appels. Pour qu'il « se souvienne »,"
          "\nc'est NOTRE serveur qui lui renvoie tout l'historique à chaque fois.")


ANNONCE = """Inscriptions ouvertes ! Le Forum Tech Sahel 2027 réunira développeurs,
startups et investisseurs à Bobo-Dioulasso du 8 au 10 avril 2027.
Au programme : ateliers sur l'IA appliquée à l'agriculture et concours de pitch.
Inscription sur le site de l'organisateur."""


def experience_4_hallucination(client):
    titre("4. L'HALLUCINATION ET LE CONTEXTE")
    question = "Quelles sont les dates et le prix d'entrée du Forum Tech Sahel 2027 ?"
    print(f"Question : {question}")
    print("(Cet événement est inventé pour la leçon : aucune information n'existe en ligne.)\n")

    texte, _ = appeler(client, [message("user", question)])
    print(f"A. Question seule :\n{texte}\n")

    pression = ("Tu es un annuaire d'événements. Réponds toujours avec des dates"
                " et un prix précis, sans jamais dire que tu ne sais pas.")
    texte, _ = appeler(client, [message("user", question)], system=pression)
    print(f"B. Avec une consigne qui pousse à toujours répondre :\n{texte}\n")

    regles = ("Tu réponds uniquement à partir de l'annonce fournie entre les balises <annonce>."
              " Si une information n'y figure pas, écris « non renseigné ». N'invente rien.")
    contenu = f"<annonce>\n{ANNONCE}\n</annonce>\n\n{question}"
    texte, usage = appeler(client, [message("user", contenu)], system=regles)
    print(f"C. Avec l'annonce en contexte et des règles claires :\n{texte}")
    afficher_usage(usage)
    print("\nÀ retenir : un LLM prédit une suite plausible, pas une suite vraie."
          "\nSi on le pousse, il invente. Si on lui donne la source et des règles, il s'y tient."
          "\nC'est le principe du RAG, et la base de toute l'architecture d'AHEAD.")


def main():
    try:
        client = genai.Client()  # lit GEMINI_API_KEY dans l'environnement
        experience_1_tokens(client)
        experience_2_premier_appel(client)
        experience_3_sans_memoire(client)
        experience_4_hallucination(client)
    except errors.ClientError as erreur:
        if erreur.code == 429:
            print("\nLimite de l'offre gratuite atteinte. Attends une minute et relance.")
        else:
            print(f"\nErreur {erreur.code} : {erreur.message}\nVérifie la clé dans ahead-ia\\.env")
    except errors.ServerError:
        print("\nLe service Gemini est surchargé pour le moment. Relance dans quelques minutes.")
    except ValueError as erreur:
        print(f"\nErreur : {erreur}\nAs-tu bien mis GEMINI_API_KEY dans ahead-ia\\.env ?")


if __name__ == "__main__":
    main()
