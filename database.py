import sqlite3
import json
from datetime import datetime
from config import DB_PATH


class Database:
    @staticmethod
    def init():
        conn = sqlite3.connect(DB_PATH)
        conn.execute('''CREATE TABLE IF NOT EXISTS history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TEXT,
                            village TEXT,
                            risk_score REAL,
                            risk_level TEXT,
                            people_at_risk INTEGER,
                            rainfall_score REAL,
                            slope_score REAL,
                            soil_score REAL,
                            elevation_score REAL,
                            cloudburst_score REAL,
                            cloudburst_level TEXT,
                            glof_score REAL,
                            glof_level TEXT,
                            raw_data TEXT
                        )''')
        conn.commit()

        # ---- Safe migration for DBs created with the OLD schema ----
        # If your floodshield.db already existed before this update,
        # this adds the new columns without deleting old data.
        existing_cols = [row[1] for row in conn.execute("PRAGMA table_info(history)")]
        new_columns = {
            "timestamp": "TEXT",
            "rainfall_score": "REAL",
            "slope_score": "REAL",
            "soil_score": "REAL",
            "elevation_score": "REAL",
            "cloudburst_score": "REAL",
            "cloudburst_level": "TEXT",
            "glof_score": "REAL",
            "glof_level": "TEXT",
            "raw_data": "TEXT"
        }
        for col, col_type in new_columns.items():
            if col not in existing_cols:
                try:
                    conn.execute(f"ALTER TABLE history ADD COLUMN {col} {col_type}")
                except sqlite3.OperationalError:
                    pass  # column already exists, ignore
        conn.commit()
        conn.close()

    @staticmethod
    def save(results):
        conn = sqlite3.connect(DB_PATH)
        timestamp = datetime.now().isoformat()

        for r in results:
            breakdown = r.get("breakdown", {})
            cloudburst = r.get("cloudburst", {})
            glof = r.get("glof", {})

            conn.execute('''INSERT INTO history (
                                timestamp, village, risk_score, risk_level, people_at_risk,
                                rainfall_score, slope_score, soil_score, elevation_score,
                                cloudburst_score, cloudburst_level,
                                glof_score, glof_level, raw_data
                            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                         (
                             timestamp,
                             r['name'],
                             r['risk_score'],
                             r['risk_level'],
                             r['people_at_risk'],
                             breakdown.get('rainfall', 0),
                             breakdown.get('slope', 0),
                             breakdown.get('soil', 0),
                             breakdown.get('elevation', 0),
                             cloudburst.get('score', 0),
                             cloudburst.get('level', 'NORMAL'),
                             glof.get('score', 0),
                             glof.get('risk_level', 'NONE'),
                             json.dumps(r, default=str)  # full snapshot for deep inspection later
                         ))
        conn.commit()
        conn.close()

    @staticmethod
    def get_history(village_name=None, limit=50):
        """
        Fetch recent history, optionally filtered by village.
        Used for trend charts / history endpoint.
        """
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        if village_name:
            rows = conn.execute(
                "SELECT * FROM history WHERE village = ? ORDER BY id DESC LIMIT ?",
                (village_name, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_trend_summary(village_name):
        """
        Returns risk_score over time for a village — perfect for a line chart
        showing "risk rising over last 24 hours".
        """
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT timestamp, risk_score, risk_level, cloudburst_level, glof_level "
            "FROM history WHERE village = ? ORDER BY id ASC",
            (village_name,)
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_latest_critical_events(limit=20):
        """
        Returns most recent CRITICAL/WARNING events across all villages —
        good for an 'alert history log' on the frontend.
        """
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM history WHERE risk_level IN ('CRITICAL','WARNING') "
            "ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]