#!/usr/bin/env bash
# Restores a backup produced by backup.sh into a target database.
# The target database must already exist and be empty (or --clean is
# used to drop existing objects first); this script defaults to
# --clean --if-exists so re-running a restore is safe.
#
# Usage: DATABASE_URL=postgresql://user:pass@host:port/dbname ./scripts/restore.sh <dump_file>

set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL is not set (e.g. postgresql://seyal:<password>@localhost:5432/seyal_dev)" >&2
  exit 1
fi

DUMP_FILE="${1:-}"
if [ -z "$DUMP_FILE" ] || [ ! -f "$DUMP_FILE" ]; then
  echo "Usage: $0 <dump_file>" >&2
  exit 1
fi

PG_URL="${DATABASE_URL/postgresql+psycopg:/postgresql:}"

pg_restore --clean --if-exists --no-owner --dbname="$PG_URL" "$DUMP_FILE"
echo "Restore from $DUMP_FILE complete."
