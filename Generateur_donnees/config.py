import os

# Dossier des données. Dans l'image Docker, la variable DOSSIER_DONNEE vaut
# /app/donnees (voir le Dockerfile). Hors Docker : ./donnees par défaut.
DOSSIER_DONNEE = os.environ.get("DOSSIER_DONNEE", "donnees")

ENTETE = ["horodatage", "compteur", "batiment", "puissance_w"]

# Sujet MQTT d'une mesure, par exemple campus/batiment-A/compteur-01/puissance
SUJET = "campus/{batiment}/{compteur}/puissance"

PAS_SECONDES = 300  # une mesure toutes les 5 minutes dans les données


def chemin_fichier(nom, dossier=None):
    """Chemin du fichier d'un compteur (ou d'un bâtiment) : <dossier>/donnees_<nom>.csv"""
    return os.path.join(dossier or DOSSIER_DONNEE, f"donnees_{nom}.csv")
