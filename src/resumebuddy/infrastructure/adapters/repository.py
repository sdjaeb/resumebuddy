import json
import os
import sqlite3
from typing import List, Optional
from resumebuddy.domain.models import UserProfile, JobOpportunity
from resumebuddy.ports.repository import IProfileRepository, IJobRepository

class FileSystemProfileRepository(IProfileRepository):
    # ... (existing code)
    def save_profile(self, profile: UserProfile, path: str):
        with open(path, "w") as f:
            f.write(profile.model_dump_json(indent=2))

    def load_profile(self, path: str) -> UserProfile:
        if not os.path.exists(path):
            return UserProfile()
        with open(path, "r") as f:
            data = json.load(f)
            return UserProfile(**data)

class SQLiteJobRepository(IJobRepository):
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    score TEXT,
                    priority INTEGER,
                    url TEXT,
                    dir TEXT,
                    status TEXT,
                    resume_content TEXT,
                    cover_letter_content TEXT,
                    details_content TEXT,
                    signals_json TEXT,
                    company_grade TEXT,
                    company_mission TEXT
                )
            """)
            # Auto-migration: Check if columns exist
            cursor = conn.execute("PRAGMA table_info(jobs)")
            columns = [info[1] for info in cursor.fetchall()]
            if "resume_content" not in columns:
                conn.execute("ALTER TABLE jobs ADD COLUMN resume_content TEXT")
            if "cover_letter_content" not in columns:
                conn.execute("ALTER TABLE jobs ADD COLUMN cover_letter_content TEXT")
            if "details_content" not in columns:
                conn.execute("ALTER TABLE jobs ADD COLUMN details_content TEXT")
            if "signals_json" not in columns:
                conn.execute("ALTER TABLE jobs ADD COLUMN signals_json TEXT")
            if "company_grade" not in columns:
                conn.execute("ALTER TABLE jobs ADD COLUMN company_grade TEXT")
            if "company_mission" not in columns:
                conn.execute("ALTER TABLE jobs ADD COLUMN company_mission TEXT")

    def save_job(self, job: JobOpportunity):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO jobs (
                    id, name, score, priority, url, dir, status, 
                    resume_content, cover_letter_content, details_content, signals_json,
                    company_grade, company_mission
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.id, job.name, job.score, job.priority, job.url, job.dir, job.status,
                job.resume_content, job.cover_letter_content, job.details_content, job.signals_json,
                job.company_grade, job.company_mission
            ))

    def get_job(self, job_id: str) -> Optional[JobOpportunity]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                return JobOpportunity(
                    id=row[0], name=row[1], score=row[2], 
                    priority=row[3], url=row[4], dir=row[5], status=row[6],
                    resume_content=row[7], cover_letter_content=row[8], details_content=row[9],
                    signals_json=row[10] if len(row) > 10 else None,
                    company_grade=row[11] if len(row) > 11 else None,
                    company_mission=row[12] if len(row) > 12 else None
                )
        return None

    def list_jobs(self) -> List[JobOpportunity]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM jobs ORDER BY priority ASC, score ASC")
            return [
                JobOpportunity(
                    id=row[0], name=row[1], score=row[2], 
                    priority=row[3], url=row[4], dir=row[5], status=row[6],
                    resume_content=row[7], cover_letter_content=row[8], details_content=row[9],
                    signals_json=row[10] if len(row) > 10 else None,
                    company_grade=row[11] if len(row) > 11 else None,
                    company_mission=row[12] if len(row) > 12 else None
                ) for row in cursor.fetchall()
            ]

    def update_content(self, job_id: str, resume: Optional[str] = None, cv: Optional[str] = None, details: Optional[str] = None, signals: Optional[str] = None):
        with sqlite3.connect(self.db_path) as conn:
            if resume:
                conn.execute("UPDATE jobs SET resume_content = ? WHERE id = ?", (resume, job_id))
            if cv:
                conn.execute("UPDATE jobs SET cover_letter_content = ? WHERE id = ?", (cv, job_id))
            if details:
                conn.execute("UPDATE jobs SET details_content = ? WHERE id = ?", (details, job_id))
            if signals:
                conn.execute("UPDATE jobs SET signals_json = ? WHERE id = ?", (signals, job_id))

    def update_status(self, job_id: str, status: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
