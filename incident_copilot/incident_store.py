
"""Persist incidents in SQLite and manage their lifecycle."""

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "incidents.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT NOT NULL,
                title TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Active',
                error_count INTEGER NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                recovered_at TEXT
            )
            """
        )


def record_incident(incident: dict) -> dict:
    """Create an incident or update the active incident for its service."""
    now = datetime.now(timezone.utc).isoformat()
    service = incident["service"]
    evidence_json = json.dumps(incident["evidence"])

    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT id FROM incidents
            WHERE service = ? AND status = 'Active'
            ORDER BY id DESC LIMIT 1
            """,
            (service,),
        ).fetchone()

        if existing:
            incident_id = existing["id"]

            connection.execute(
                """
                UPDATE incidents
                SET title = ?,
                    severity = ?,
                    error_count = ?,
                    last_seen = ?,
                    evidence_json = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    incident["title"],
                    incident["severity"],
                    incident["error_count"],
                    incident["last_seen"],
                    evidence_json,
                    now,
                    incident_id,
                ),
            )
        else:
            cursor = connection.execute(
                """
                INSERT INTO incidents (
                    service, title, severity, status,
                    error_count, first_seen, last_seen,
                    evidence_json, created_at, updated_at
                )
                VALUES (?, ?, ?, 'Active', ?, ?, ?, ?, ?, ?)
                """,
                (
                    service,
                    incident["title"],
                    incident["severity"],
                    incident["error_count"],
                    incident["first_seen"],
                    incident["last_seen"],
                    evidence_json,
                    now,
                    now,
                ),
            )
            incident_id = cursor.lastrowid

        row = connection.execute(
            "SELECT * FROM incidents WHERE id = ?",
            (incident_id,),
        ).fetchone()

    return dict(row)


def recover_incident(incident_id: int) -> None:
    """Mark an active incident as recovered."""
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE incidents
            SET status = 'Recovered',
                recovered_at = ?,
                updated_at = ?
            WHERE id = ? AND status = 'Active'
            """,
            (now, now, incident_id),
        )


def recover_stale_incidents(
    recovery_after_seconds: int = 30,
) -> int:
    """
    Recover active incidents whose last detected error is old enough.

    Returns the number of incidents recovered.
    """
    if recovery_after_seconds < 1:
        raise ValueError("recovery_after_seconds must be at least 1")

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=recovery_after_seconds)
    recovered_count = 0

    with get_connection() as connection:
        active_incidents = connection.execute(
            """
            SELECT id, last_seen
            FROM incidents
            WHERE status = 'Active'
            """
        ).fetchall()

        for incident in active_incidents:
            try:
                last_seen = datetime.fromisoformat(
                    incident["last_seen"].replace("Z", "+00:00")
                )

                if last_seen.tzinfo is None:
                    last_seen = last_seen.replace(
                        tzinfo=timezone.utc
                    )

                if last_seen <= cutoff:
                    connection.execute(
                        """
                        UPDATE incidents
                        SET status = 'Recovered',
                            recovered_at = ?,
                            updated_at = ?
                        WHERE id = ? AND status = 'Active'
                        """,
                        (
                            now.isoformat(),
                            now.isoformat(),
                            incident["id"],
                        ),
                    )
                    recovered_count += 1

            except (ValueError, TypeError):
                # Keep the incident active if its timestamp is invalid.
                continue

    return recovered_count


def list_incidents(limit: int = 50) -> list[dict]:
    """Return the most recent incidents, including their evidence."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM incidents
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    incidents = []

    for row in rows:
        item = dict(row)
        item["evidence"] = json.loads(
            item.pop("evidence_json")
        )
        incidents.append(item)

    return incidents


initialize_database()
