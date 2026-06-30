import os
import shutil
from datetime import datetime, timezone


def backup_database(db_path, backup_dir):
    """Copy the live SQLite database file to a timestamped backup file.

    Returns the path to the created backup file, or None if there is no
    SQLite database to back up (e.g. running on Postgres in production).
    """
    if not db_path or not os.path.exists(db_path):
        return None

    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_filename = f"inventory-backup-{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    shutil.copy2(db_path, backup_path)
    return backup_path


def restore_database(db_path, uploaded_file_path):
    """Replace the live SQLite database file with an uploaded backup file."""
    if not db_path:
        raise ValueError("No SQLite database is configured for this environment.")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    shutil.copy2(uploaded_file_path, db_path)
    return db_path
