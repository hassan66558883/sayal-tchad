#!/usr/bin/env bash
# Dumps the SEYAL-TCHAD database to a timestamped, compressed file using
# pg_dump's custom format (-Fc), which pg_restore can apply selectively
# and which is portable across machines/architectures.
#
# Usage: DATABASE_URL=postgresql://user:pass@host:port/dbname ./scripts/backup.sh [output_dir]

set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL is not set (e.g. postgresql://seyal:<password>@localhost:5432/seyal_dev)" >&2
  exit 1
fi

OUTPUT_DIR="${1:-./backups}"
mkdir -p "$OUTPUT_DIR"

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUTPUT_FILE="$OUTPUT_DIR/seyal-tchad-$TIMESTAMP.dump"

# pg_dump accepts a plain postgresql:// URL; strip a SQLAlchemy-style
# "+psycopg" driver suffix if present (DATABASE_URL is often shared
# between the app and these scripts).
PG_URL="${DATABASE_URL/postgresql+psycopg:/postgresql:}"

pg_dump --format=custom --file="$OUTPUT_FILE" "$PG_URL"
echo "Backup written to $OUTPUT_FILE"
