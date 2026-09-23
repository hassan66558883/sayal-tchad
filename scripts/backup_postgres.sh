#!/usr/bin/env bash
# SEYAL-TCHAD ERP - sauvegarde de la base PostgreSQL (sauvegarde et plan de
# reprise d'activite).
#
# Usage: scripts/backup_postgres.sh <db_name> [backup_dir] [retention_days]
#
# Produit un dump au format "custom" pg_dump (-Fc, compresse, restaurable
# selectivement avec pg_restore) dans <backup_dir> (./backups par defaut).
# Les fichiers de <db_name> plus vieux que <retention_days> jours (14 par
# defaut) sont supprimes automatiquement apres la sauvegarde.
#
# Lit DB_USER depuis .env si present (jamais de mot de passe en dur dans le
# code source - le mot de passe n'est pas necessaire ici car le dump s'execute a
# l'interieur du conteneur "db" via docker compose exec, sans passer par le
# reseau ni par une variable en clair sur la ligne de commande).
set -euo pipefail

DB_NAME="${1:?Usage: $0 <db_name> [backup_dir] [retention_days]}"
BACKUP_DIR="${2:-./backups}"
RETENTION_DAYS="${3:-14}"

cd "$(dirname "$0")/.."

if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    . ./.env
    set +a
fi
DB_USER="${DB_USER:-odoo}"

mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUT_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.dump"

echo "Sauvegarde de la base '$DB_NAME' vers $OUT_FILE ..."
docker compose exec -T db pg_dump -U "$DB_USER" -Fc -d "$DB_NAME" > "$OUT_FILE"
echo "Sauvegarde creee : $OUT_FILE ($(du -h "$OUT_FILE" | cut -f1))"

DELETED=$(find "$BACKUP_DIR" -name "${DB_NAME}_*.dump" -mtime "+${RETENTION_DAYS}" -print -delete)
if [ -n "$DELETED" ]; then
    echo "Sauvegardes de plus de ${RETENTION_DAYS} jours supprimees :"
    echo "$DELETED"
fi
