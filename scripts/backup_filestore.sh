#!/usr/bin/env bash
# SEYAL-TCHAD ERP - sauvegarde du filestore Odoo (pieces jointes : factures PDF,
# recus, photos de compteurs, etc.) (sauvegarde et plan de reprise d'activite).
#
# Usage: scripts/backup_filestore.sh [backup_dir] [retention_days]
#
# Le filestore vit dans le volume Docker monte sur /var/lib/odoo du
# conteneur "odoo" (voir docker-compose.yml). Ce script resout le nom reel
# de ce volume via `docker inspect` (plutot que de supposer un prefixe de
# projet fixe), puis en fait une archive tar.gz horodatee dans
# <backup_dir> (./backups par defaut). Les archives plus vieilles que
# <retention_days> jours (14 par defaut) sont supprimees automatiquement.
set -euo pipefail

# Sous Git Bash (Windows), les arguments commencant par "/" (ex: "-v
# host:/data") sont sinon reecrits en chemins Windows par MSYS, ce qui
# casse le montage du volume Docker. Sans effet sur Linux/Mac.
export MSYS_NO_PATHCONV=1

BACKUP_DIR="${1:-./backups}"
RETENTION_DAYS="${2:-14}"

cd "$(dirname "$0")/.."
mkdir -p "$BACKUP_DIR"

ODOO_CONTAINER="$(docker compose ps -q odoo)"
if [ -z "$ODOO_CONTAINER" ]; then
    echo "Le conteneur 'odoo' n'est pas demarre (docker compose up -d requis)." >&2
    exit 1
fi

VOLUME_NAME="$(docker inspect -f '{{ range .Mounts }}{{ if eq .Destination "/var/lib/odoo" }}{{ .Name }}{{ end }}{{ end }}' "$ODOO_CONTAINER")"
if [ -z "$VOLUME_NAME" ]; then
    echo "Impossible de trouver le volume monte sur /var/lib/odoo." >&2
    exit 1
fi

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUT_FILE="$BACKUP_DIR/filestore_${TIMESTAMP}.tar.gz"

echo "Sauvegarde du volume '$VOLUME_NAME' vers $OUT_FILE ..."
docker run --rm \
    -v "${VOLUME_NAME}:/data:ro" \
    -v "$(pwd)/${BACKUP_DIR}:/backup" \
    alpine sh -c "tar czf /backup/$(basename "$OUT_FILE") -C /data ."
echo "Sauvegarde creee : $OUT_FILE ($(du -h "$OUT_FILE" | cut -f1))"

DELETED=$(find "$BACKUP_DIR" -name "filestore_*.tar.gz" -mtime "+${RETENTION_DAYS}" -print -delete)
if [ -n "$DELETED" ]; then
    echo "Sauvegardes de plus de ${RETENTION_DAYS} jours supprimees :"
    echo "$DELETED"
fi
