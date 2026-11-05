"""
Leçon 1 : comment fonctionne un LLM.

Quatre expériences :
  1. Les tokens : ce que le modèle lit vraiment.
  2. Un premier appel, avec son coût.
  3. Pas de mémoire : chaque appel repart de zéro.
  4. L'hallucination, et comment le contexte la corrige (l'idée du RAG).

Lancer depuis le dossier ahead-ia :
    .venv\\Scripts\\python.exe lecons\\01_premier_appel.py
"""
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MODELE = "claude-opus-5-5"
PRIX_ENTREE = 4.00 / 1_000_000  # dollars par token envoyé au modèle
PRIX_SORTIE = 20.00 / 1_000_000  # dollars par token produit par le modèle


def appeler(client, messages, system=None, effort="low"):
    """Envoie une conversation au modèle. Renvoie le texte et l'usage en tokens."""
    options = {}
    if system:
        options["system"] = system
    reponse = client.beta.messages.create(
        model=MODELE,
        max_tokens=2000,
        messages=messages,
        # effort : combien le modèle réfléchit avant de répondre (low, medium, high...)
        output_config={"effort": effort},
        # Si le modèle principal refuse pour une raison de sécurité, un autre prend le relais.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        **options,
    )
    if reponse.stop_reason == "refusal":
        return "[le modèle a refusé de répondre]", reponse.usage
    # La réponse est une liste de blocs ; on ne garde que les blocs de texte.
    texte = "".join(bloc.text for bloc in reponse.content if bloc.type == "text")
    return texte, reponse.usage


def afficher_cout(usage):
    cout = usage.input_tokens * PRIX_ENTREE + usage.output_tokens * PRIX_SORTIE
    print(f"   -> {usage.input_tokens} tokens envoyés, {usage.output_tokens} tokens produits,"
          f" coût : {cout:.5f} $")


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
        compte = client.messages.count_tokens(
            model=MODELE, messages=[{"role": "user", "content": phrase}]
        )
        # Le compte inclut quelques tokens techniques autour du message.
        print(f"{langue:9} : {len(phrase)} caractères -> {compte.input_tokens} tokens")
    print("\nÀ retenir : le modèle ne lit pas des lettres mais des morceaux de mots."
          "\nOn paie au token, et la même idée ne coûte pas pareil selon la langue.")


def experience_2_premier_appel(client):
    titre("2. UN PREMIER APPEL")
    question = "En deux phrases, qu'est-ce qu'un salon professionnel ?"
    print(f"Question : {question}\n")
    texte, usage = appeler(client, [{"role": "user", "content": question}])
    print(texte)
    afficher_cout(usage)
    print("\nÀ retenir : les tokens produits coûtent 5 fois plus cher que les tokens envoyés."
          "\nLa réflexion interne du modèle compte dans les tokens produits.")


def experience_3_sans_memoire(client):
    titre("3. PAS DE MÉMOIRE")
    presentation = {"role": "user", "content": "Je m'appelle Jennifer et je travaille sur AHEAD."}
    question = {"role": "user", "content": "Comment je m'appelle ? Réponds en une phrase."}

    texte, _ = appeler(client, [presentation])
    print(f"Appel 1 (présentation) : {texte}\n")

    texte, _ = appeler(client, [question])
    print(f"Appel 2 (question seule) : {texte}\n")

    historique = [presentation, {"role": "assistant", "content": "Enchantée, Jennifer !"}, question]
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

    texte, _ = appeler(client, [{"role": "user", "content": question}])
    print(f"A. Question seule :\n{texte}\n")

    pression = ("Tu es un annuaire d'événements. Réponds toujours avec des dates"
                " et un prix précis, sans jamais dire que tu ne sais pas.")
    texte, _ = appeler(client, [{"role": "user", "content": question}], system=pression)
    print(f"B. Avec une consigne qui pousse à toujours répondre :\n{texte}\n")

    regles = ("Tu réponds uniquement à partir de l'annonce fournie entre les balises <annonce>."
              " Si une information n'y figure pas, écris « non renseigné ». N'invente rien.")
    message = f"<annonce>\n{ANNONCE}\n</annonce>\n\n{question}"
    texte, usage = appeler(client, [{"role": "user", "content": message}], system=regles)
    print(f"C. Avec l'annonce en contexte et des règles claires :\n{texte}")
    afficher_cout(usage)
    print("\nÀ retenir : un LLM prédit une suite plausible, pas une suite vraie."
          "\nSi on le pousse, il invente. Si on lui donne la source et des règles, il s'y tient."
          "\nC'est le principe du RAG, et la base de toute l'architecture d'AHEAD.")


def main():
    try:
        client = anthropic.Anthropic()
        experience_1_tokens(client)
        experience_2_premier_appel(client)
        experience_3_sans_memoire(client)
        experience_4_hallucination(client)
    except anthropic.AuthenticationError:
        print("\nClé d'API invalide. Vérifie le fichier ahead-ia\\.env")
    except anthropic.APIConnectionError:
        print("\nImpossible de joindre l'API. Vérifie la connexion internet.")
    except anthropic.AnthropicError as erreur:
        print(f"\nErreur : {erreur}\nAs-tu bien créé le fichier ahead-ia\\.env avec ta clé ?")


if __name__ == "__main__":
    main()
