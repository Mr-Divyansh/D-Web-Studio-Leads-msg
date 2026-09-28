"""Lead repository for SQLite database persistence and querying."""

from __future__ import annotations

import sqlite3
from typing import Any

from app.database.db import get_connection, transaction
from app.leads.importer import LeadRecord
from app.logging import get_logger

log = get_logger("app.leads.repository")


class LeadRepository:
    def __init__(self, conn: sqlite3.Connection | None = None):
        self._conn = conn

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn
        return get_connection()

    def upsert_many(self, leads: list[LeadRecord]) -> int:
        """Insert leads; if identity_key exists, update non-conflicting fields."""
        inserted = 0
        sql = """
            INSERT INTO leads (
                id, identity_key, name, email, email_raw, phone, phone_raw,
                is_priority, gender, age, city, education, source, unverified_notes,
                email_status, whatsapp_status, overall_status, is_opted_out
            ) VALUES (
                :id, :identity_key, :name, :email, :email_raw, :phone, :phone_raw,
                :is_priority, :gender, :age, :city, :education, :source, :unverified_notes,
                :email_status, :whatsapp_status, :overall_status, :is_opted_out
            )
            ON CONFLICT(identity_key) DO UPDATE SET
                email = coalesce(excluded.email, leads.email),
                phone = coalesce(excluded.phone, leads.phone),
                is_priority = max(excluded.is_priority, leads.is_priority),
                unverified_notes = coalesce(excluded.unverified_notes, leads.unverified_notes),
                updated_at = CURRENT_TIMESTAMP;
        """
        with transaction():
            for lead in leads:
                self.conn.execute(sql, lead.to_db_row())
                inserted += 1
        log.info("Saved %d leads to database", inserted)
        return inserted

    def count_all(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) FROM leads;")
        return cursor.fetchone()[0]

    def count_priority(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) FROM leads WHERE is_priority = 1;")
        return cursor.fetchone()[0]

    def get_summary_counts(self) -> dict[str, int]:
        row = self.conn.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN is_priority = 1 THEN 1 ELSE 0 END) AS priority,
                SUM(CASE WHEN overall_status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed,
                SUM(CASE WHEN overall_status = 'PENDING' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN overall_status = 'FAILED' THEN 1 ELSE 0 END) AS failed,
                SUM(CASE WHEN email_status = 'SENT' THEN 1 ELSE 0 END) AS email_sent,
                SUM(CASE WHEN whatsapp_status = 'SENT' THEN 1 ELSE 0 END) AS whatsapp_sent,
                SUM(CASE WHEN is_opted_out = 1 THEN 1 ELSE 0 END) AS opted_out
            FROM leads;
        """).fetchone()
        return {k: (row[k] or 0) for k in row.keys()}

    def get_eligible_leads(
        self,
        priority_only: bool = True,
        limit: int | None = None,
    ) -> list[sqlite3.Row]:
        """Fetch pending leads that are not opted out and have at least one reachable channel."""
        query = """
            SELECT * FROM leads
            WHERE is_opted_out = 0
              AND overall_status IN ('PENDING', 'PROCESSING')
              AND (email_status = 'PENDING' OR whatsapp_status = 'PENDING')
        """
        params: list[Any] = []
        if priority_only:
            query += " AND is_priority = 1"
        query += " ORDER BY is_priority DESC, created_at ASC"
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        return self.conn.execute(query, params).fetchall()

    def get_by_id(self, lead_id: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM leads WHERE id = ?;", (lead_id,)).fetchone()

    def update_channel_status(
        self,
        lead_id: str,
        channel: str,
        status: str,
    ) -> None:
        """Update a lead's channel status ('email' or 'whatsapp') and recalculate overall_status."""
        col = "email_status" if channel == "email" else "whatsapp_status"
        with transaction():
            self.conn.execute(
                f"UPDATE leads SET {col} = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (status, lead_id),
            )
            # Recompute overall_status
            lead = self.conn.execute("SELECT email_status, whatsapp_status FROM leads WHERE id = ?;", (lead_id,)).fetchone()
            if lead:
                e_stat = lead["email_status"]
                w_stat = lead["whatsapp_status"]
                # Completed if both reachable channels are sent (or not available)
                all_done = (
                    e_stat in {"SENT", "NOT_AVAILABLE"} and
                    w_stat in {"SENT", "NOT_AVAILABLE", "SKIPPED"}
                )
                any_failed = e_stat == "FAILED" or w_stat == "FAILED"
                new_overall = "COMPLETED" if all_done else ("FAILED" if any_failed else "PROCESSING")
                self.conn.execute(
                    "UPDATE leads SET overall_status = ? WHERE id = ?;",
                    (new_overall, lead_id),
                )