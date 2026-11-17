#!/usr/bin/env python3
"""Rejeu PROVISOIRE : publie les mesures d'un compteur sur un broker MQTT, en accéléré.

ATTENTION : ce script n'est PAS le rejeu.py fourni par l'enseignant.

Configuration par variables d'environnement (un argument passe avant la variable) :
  COMPTEUR        identité du conteneur ; sert à trouver le fichier et à nommer le client MQTT
  DOSSIER_DONNEE  dossier des données (voir config.py)
  FICHIER         chemin complet du fichier, pour un cas particulier
  MQTT_HOST       adresse du broker (défaut : localhost)
  MQTT_USER, MQTT_PASSWORD   identifiants, facultatifs pour l'instant
  PAUSE           secondes réelles entre deux pas de 5 minutes des données
  DEPART          instant de départ commun (secondes Unix) pour synchroniser les compteurs

Exemple sans broker :
  COMPTEUR=compteur-01 python3 rejeu_provisoire.py --simulation --pause 0
"""
import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime

import config

journal = logging.getLogger("rejeu")


def lire_mesures(chemin):
    with open(chemin, newline="") as f:
        yield from csv.DictReader(f)


def lire_arguments():
    compteur = os.environ.get("COMPTEUR")
    defaut = config.chemin_fichier(compteur) if compteur else None
    depart = os.environ.get("DEPART")

    p = argparse.ArgumentParser(description="Rejeu provisoire de mesures vers MQTT")
    p.add_argument("--fichier", default=os.environ.get("FICHIER", defaut))
    p.add_argument("--hote", default=os.environ.get("MQTT_HOST", "localhost"))
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--pause", type=float, default=float(os.environ.get("PAUSE", "1.0")),
                   help="secondes réelles entre deux pas de temps des données")
    p.add_argument("--depart", type=float, default=float(depart) if depart else None,
                   help="instant de départ commun, en secondes Unix (date +%%s)")
    p.add_argument("--simulation", action="store_true",
                   help="affiche les messages sans se connecter au broker")
    args = p.parse_args()
    if not args.fichier:
        p.error("indiquer --fichier, ou la variable FICHIER ou COMPTEUR")
    args.compteur = compteur
    return args


def connecter(args):
    import paho.mqtt.client as mqtt
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=args.compteur or "")
    utilisateur = os.environ.get("MQTT_USER")
    if utilisateur:
        client.username_pw_set(utilisateur, os.environ.get("MQTT_PASSWORD"))
    client.connect(args.hote, args.port)
    client.loop_start()
    journal.info("connecté au broker %s:%s", args.hote, args.port)
    return client


def rejouer(args, client):
    """Publie chaque mesure à son heure et retourne le nombre de messages envoyés."""
    nb = 0
    depart = args.depart if args.depart else time.time()
    origine = None  # horodatage de la première mesure du fichier
    for ligne in lire_mesures(args.fichier):
        # Heure d'envoi calculée à partir du départ commun : des compteurs lancés
        # avec le même DEPART et la même PAUSE restent alignés, sans dérive.
        instant = datetime.fromisoformat(ligne["horodatage"])
        if origine is None:
            origine = instant
        pas = (instant - origine).total_seconds() / config.PAS_SECONDES
        attente = depart + pas * args.pause - time.time()
        if attente > 0:
            time.sleep(attente)

        sujet = config.SUJET.format(**ligne)
        message = json.dumps({
            "horodatage": ligne["horodatage"],   # heure de la mesure, pas de l'envoi
            "compteur": ligne["compteur"],
            "batiment": ligne["batiment"],
            "puissance_w": float(ligne["puissance_w"]),
        })
        if client is None:
            print(sujet, message)
        else:
            client.publish(sujet, message, qos=1).wait_for_publish()
        nb += 1
        if nb == 1 or nb % 50 == 0:
            journal.info("%d messages envoyés (temps des données : %s)", nb, ligne["horodatage"])
    return nb


def main():
    args = lire_arguments()
    logging.basicConfig(
        stream=sys.stderr, level=logging.INFO,
        format=f"%(asctime)s [{args.compteur or 'rejeu'}] %(message)s", datefmt="%H:%M:%S")

    journal.info("démarrage : fichier=%s pause=%ss depart=%s", args.fichier, args.pause,
                 args.depart if args.depart else "immédiat")
    if not os.path.exists(args.fichier):
        journal.error("fichier introuvable : %s (vérifier COMPTEUR et DOSSIER_DONNEE)", args.fichier)
        sys.exit(1)

    client = None if args.simulation else connecter(args)
    nb = 0
    try:
        nb = rejouer(args, client)
    except KeyboardInterrupt:
        journal.info("rejeu interrompu")
    finally:
        if client is not None:
            client.loop_stop()
            client.disconnect()
    journal.info("terminé : %d messages envoyés", nb)


if __name__ == "__main__":
    main()