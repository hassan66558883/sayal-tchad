#!/usr/bin/env bash
# SEYAL-TCHAD ERP - restauration d'une sauvegarde PostgreSQL (section 20).
#
# Usage: scripts/restore_postgres.sh <fichier.dump> <db_name_cible>
#
# Cree <db_name_cible> (doit ne pas deja exister) et y restaure le dump
# produit par backup_postgres.sh. Sert aussi bien a recuperer d'un
# incident qu'a verifier periodiquement qu'une sauvegarde est utilisable
# (restauration d'essai vers une base de test).
set -euo pipefail

DUMP_FILE="${1:?Usage: $0 <fichier.dump> <db_name_cible>}"
TARGET_DB="${2:?Usage: $0 <fichier.dump> <db_name_cible>}"

cd "$(dirname "$0")/.."

if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    . ./.env
    set +a
fi
DB_USER="${DB_USER:-odoo}"

if [ ! -f "$DUMP_FILE" ]; then
    echo "Fichier de sauvegarde introuvable : $DUMP_FILE" >&2
    exit 1
fi

echo "Creation de la base '$TARGET_DB' ..."
docker compose exec -T db createdb -U "$DB_USER" "$TARGET_DB"

echo "Restauration de $DUMP_FILE vers '$TARGET_DB' ..."
docker compose exec -T db pg_restore -U "$DB_USER" -d "$TARGET_DB" --no-owner < "$DUMP_FILE"

echo "Restauration terminee : base '$TARGET_DB'."
