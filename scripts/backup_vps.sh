
#!/usr/bin/env bash
set -Eeuo pipefail

# Cadangan CIG: database, foto scanner, dan gambar konten.
# Jalankan pada VPS Linux yang sudah menjalankan Docker Compose.

umask 077

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_ROOT="${CIG_BACKUP_DIR:-/opt/cig-backups}"
TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"
BACKUP_DEST="$BACKUP_ROOT/$TIMESTAMP"

mkdir -p "$BACKUP_ROOT"
chmod 700 "$BACKUP_ROOT"

TEMP_DIR="$(mktemp -d "$BACKUP_ROOT/.backup-temp-XXXXXX")"
trap 'rm -rf -- "$TEMP_DIR"' EXIT

cd "$PROJECT_DIR"

echo "[1/4] Backup PostgreSQL..."
docker compose exec -T db \
  pg_dump -U cig -d cig -Fc \
  > "$TEMP_DIR/database.dump"

echo "[2/4] Backup foto AI Scanner..."
docker compose exec -T web \
  tar -C /app/instance -czf - . \
  > "$TEMP_DIR/scan_files.tar.gz"

echo "[3/4] Backup gambar modul, kuis, dan resep..."
docker compose exec -T web \
  tar -C /app/app/static/uploads -czf - . \
  > "$TEMP_DIR/content_uploads.tar.gz"

echo "[4/4] Verifikasi file backup..."
docker compose exec -T db \
  pg_restore -l \
  < "$TEMP_DIR/database.dump" > /dev/null

tar -tzf "$TEMP_DIR/scan_files.tar.gz" > /dev/null
tar -tzf "$TEMP_DIR/content_uploads.tar.gz" > /dev/null

(
  cd "$TEMP_DIR"
  sha256sum \
    database.dump \
    scan_files.tar.gz \
    content_uploads.tar.gz \
    > SHA256SUMS
)

mv "$TEMP_DIR" "$BACKUP_DEST"
trap - EXIT

echo "BACKUP BERHASIL"
echo "Lokasi: $BACKUP_DEST"
