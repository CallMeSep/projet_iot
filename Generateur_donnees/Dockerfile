FROM python:3.11-alpine
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup -S appgroup && adduser -S -G appgroup appuser
COPY config.py compteur.py rejeu_provisoire.py ./

ENV PYTHONUNBUFFERED=1
# Seul endroit où le dossier des données est défini pour l'image.
ENV DOSSIER_DONNEE=/app/data

# Données générées pendant la construction, avant de changer d'utilisateur.
ARG GRAINE=42
ARG JOURS=2
RUN python compteur.py --graine "$GRAINE" --jours "$JOURS"

USER appuser

# Le rejeu trouve son fichier avec DOSSIER_DONNEE (image) et COMPTEUR (Compose).
CMD ["python", "rejeu_provisoire.py"]