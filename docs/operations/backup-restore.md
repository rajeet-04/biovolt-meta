# Backup and restore

Create a consistent SQLite backup with `python scripts/backup_biovolt.py /data/biovolt.db backups/biovolt.db`, then restore to a new path with `python scripts/restore_biovolt_backup.py backups/biovolt.db acceptance/biovolt.db`. Never use `docker compose down -v` during recovery: it deletes the persistent volume. Validate experiment identity, calibration provenance, and safe exports after restore.
