#!/usr/bin/env python3
"""Générateur PROVISOIRE de données pour le cas A (énergie).

ATTENTION : ce script n'est PAS le generer_donnees.py fourni par l'enseignant.
Le format (colonnes, identifiants, anomalies) est une hypothèse. Il sert à
monter la plateforme en attendant le script officiel, à utiliser pour le rendu.

Exemples :
  python3 compteur.py --graine 42                    # un fichier par compteur
  python3 compteur.py --graine 42 --par batiment     # un fichier par bâtiment
  python3 compteur.py --graine 42 --jours 1 --dossier output
"""
import argparse
import csv
import math
import os
import random
from datetime import datetime, timedelta, timezone

COMPTEURS = [  # (identifiant, bâtiment, puissance de base en watts)
    ("compteur-01", "batiment-A", 1800),
    ("compteur-02", "batiment-A", 2500),
    ("compteur-03", "batiment-B", 1200),
    ("compteur-04", "batiment-B", 5000)
]
PAS = timedelta(minutes=5)
ENTETE = ["horodatage", "compteur", "batiment", "puissance_w"]
COLONNE = {"compteur": 1, "batiment": 2}  # position de la colonne dans une ligne


def puissance_normale(base, instant, rng):
    """Consommation plus forte en journée, avec un peu de bruit."""
    heure = instant.hour + instant.minute / 60
    cycle = 0.5 + 0.5 * math.sin((heure - 8) / 24 * 2 * math.pi)
    return round(base * (0.6 + 0.8 * cycle) + rng.gauss(0, base * 0.05), 1)


def generer(graine, jours):
    rng = random.Random(graine)
    debut = datetime(2026, 11, 2, tzinfo=timezone.utc)
    nb_points = int(timedelta(days=jours) / PAS)

    # Une anomalie de chaque type, placée selon la graine.
    c_depassement, c_muet, c_impossible = rng.sample(range(len(COMPTEURS)), 3)
    i_depassement = rng.randrange(nb_points // 4, nb_points // 2)
    i_muet = rng.randrange(nb_points // 2, nb_points - 30)
    i_impossible = rng.randrange(10, nb_points - 10)

    lignes = []
    for i in range(nb_points):
        instant = debut + i * PAS
        for c, (ident, batiment, base) in enumerate(COMPTEURS):
            valeur = puissance_normale(base, instant, rng)
            if c == c_depassement and i_depassement <= i < i_depassement + 12:
                valeur = round(valeur * 3, 1)          # dépassement pendant 1 h
            if c == c_muet and i_muet <= i < i_muet + 24:
                continue                               # compteur muet pendant 2 h
            if c == c_impossible and i == i_impossible:
                valeur = -500.0                        # valeur impossible
            lignes.append((instant.isoformat(), ident, batiment, valeur))
    return lignes


def main():
    p = argparse.ArgumentParser(description="Générateur provisoire de données (cas A)")
    p.add_argument("--graine", type=int, required=True, help="graine de l'équipe")
    p.add_argument("--jours", type=int, default=2)
    p.add_argument("--dossier", default=os.environ.get("DOSSIER_DONNEE", "app/donnees"), help="dossier où écrire les fichiers")
    p.add_argument("--par", choices=["compteur", "batiment"], default="compteur",
                   help="un fichier par compteur (défaut) ou par bâtiment")
    args = p.parse_args()

    lignes = generer(args.graine, args.jours)
    os.makedirs(args.dossier, exist_ok=True)   # crée le dossier s'il n'existe pas

    # Un fichier par compteur (donnees_compteur-01.csv...) ou par bâtiment.
    col = COLONNE[args.par]
    for nom in sorted({ligne[col] for ligne in lignes}):
        chemin = os.path.join(args.dossier, f"donnees_{nom}.csv")
        selection = [ligne for ligne in lignes if ligne[col] == nom]
        with open(chemin, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(ENTETE)
            w.writerows(selection)
        print(f"{len(selection)} mesures écrites dans {chemin}")


if __name__ == "__main__":
    main()