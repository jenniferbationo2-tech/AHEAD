"""
Le format des fiches événement, partagé par tout le projet.

FicheReference est la fiche « vérité » : celle qu'un humain a corrigée à la main.
Elle sert de base à l'assistant et de réponse attendue pour mesurer l'extraction.
"""
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

THEMES = Literal[
    "Intelligence artificielle", "Développement logiciel", "Données",
    "Cybersécurité", "Robotique", "Agriculture", "Santé numérique",
    "Entrepreneuriat", "Financement", "Autre",
]

FORMATS = Literal["présentiel", "en ligne", "hybride"]


class FicheReference(BaseModel):
    # extra="forbid" : une faute de frappe dans un nom de champ est signalée.
    model_config = {"extra": "forbid"}

    est_un_evenement: bool
    nom: str | None = None
    date_debut: date | None = None
    date_fin: date | None = None
    lieu: str | None = None
    format: FORMATS | None = None
    organisateur: str | None = None
    prix: str | None = Field(None, description="Montant et devise, ou « gratuit ».")
    themes: list[THEMES] = []

    @model_validator(mode="after")
    def coherence(self):
        if self.date_debut and self.date_fin and self.date_fin < self.date_debut:
            raise ValueError("date_fin est avant date_debut")
        if self.est_un_evenement and not self.themes:
            raise ValueError("un événement doit avoir au moins un thème")
        return self


class Metadonnees(BaseModel):
    """Ce qu'on sait de l'annonce elle-même (fourni par la collecte d'Élie)."""
    model_config = {"extra": "forbid"}

    source_url: str
    date_collecte: date
    langue: Literal["fr", "en", "autre"]
