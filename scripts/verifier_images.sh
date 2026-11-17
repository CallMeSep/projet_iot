#!/bin/sh
# Échoue si une image Docker n'a pas de version fixée (absente ou "latest").
# Utilisé par le pipeline, et lançable en local : ./scripts/verifier_images.sh
set -eu

erreur=0

# docker-compose.yml : chaque ligne "image:" doit avoir un tag, différent de latest
if grep -nE '^[[:space:]]*image:[[:space:]]*[^:[:space:]]+[[:space:]]*$|^[[:space:]]*image:.*:latest' docker-compose.yml; then
  echo "ERREUR : image sans version fixée dans docker-compose.yml (voir ci-dessus)"
  erreur=1
fi

# Dockerfiles : chaque ligne FROM doit avoir un tag, différent de latest
for f in $(find . -name Dockerfile -not -path './.git/*'); do
  if grep -nE '^FROM[[:space:]]+[^:[:space:]]+([[:space:]]|$)|^FROM[[:space:]]+[^[:space:]]*:latest' "$f"; then
    echo "ERREUR : image de base sans version fixée dans $f (voir ci-dessus)"
    erreur=1
  fi
done

if [ "$erreur" -eq 0 ]; then
  echo "OK : toutes les images ont une version fixée"
fi
exit "$erreur"