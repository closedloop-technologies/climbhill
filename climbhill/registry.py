from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    repo_path TEXT NOT NULL,
    base_commit TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    summary TEXT NOT NULL,
    branch TEXT,
    base_commit TEXT,
    head_commit TEXT,
    patch_path TEXT,
    status TEXT NOT NULL DEFAULT 'registered',
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    command TEXT,
    status TEXT NOT NULL,
    score REAL,
    logs_path TEXT,
    failure_reason TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(candidate_id) REFERENCES candidates(id)
);

CREATE TABLE IF NOT EXISTS costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER,
    candidate_id INTEGER,
    agent TEXT,
    model TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    tool_calls INTEGER,
    wall_clock_seconds REAL,
    estimated_usd REAL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS candidate_lineage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    relationship TEXT NOT NULL,
    related_candidate_id INTEGER,
    note TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(candidate_id) REFERENCES candidates(id)
);

CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    candidate_id INTEGER,
    decision_type TEXT NOT NULL,
    rationale TEXT,
    actor TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    path TEXT NOT NULL,
    format TEXT NOT NULL,
    summary TEXT,
    recommendation TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS issue_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    labels TEXT,
    priority TEXT,
    evidence TEXT,
    source_run_ids TEXT,
    source_candidate_ids TEXT,
    created_at TEXT NOT NULL
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class RunRecord:
    id: int
    goal: str
    status: str
    repo_path: str
    base_commit: str
    created_at: str


@dataclass(frozen=True)
class CandidateRecord:
    id: int
    run_id: int
    summary: str
    branch: str
    base_commit: str
    head_commit: str
    patch_path: str
    status: str
    created_at: str


@dataclass(frozen=True)
class CostRecord:
    id: int
    run_id: int | None
    candidate_id: int | None
    agent: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    tool_calls: int | None
    wall_clock_seconds: float | None
    estimated_usd: float | None
    created_at: str


@dataclass(frozen=True)
class LineageRecord:
    id: int
    candidate_id: int
    relationship: str
    related_candidate_id: int | None
    note: str
    created_at: str


@dataclass(frozen=True)
class DecisionRecord:
    id: int
    run_id: int
    candidate_id: int | None
    decision_type: str
    rationale: str
    actor: str
    created_at: str


@dataclass(frozen=True)
class IssueProposalRecord:
    id: int
    title: str
    body: str
    labels: str
    priority: str
    evidence: str
    source_run_ids: str
    source_candidate_ids: str
    created_at: str


class Registry:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def create_run(self, goal: str, repo_path: Path, base_commit: str = "") -> int:
        cursor = self.connection.execute(
            "INSERT INTO runs(goal, repo_path, base_commit, created_at) VALUES (?, ?, ?, ?)",
            (goal, str(repo_path), base_commit, utc_now()),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def get_run(self, run_id: int) -> Optional[RunRecord]:
        row = self.connection.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            return None
        return RunRecord(**dict(row))

    def list_runs(self) -> List[RunRecord]:
        rows = self.connection.execute("SELECT * FROM runs ORDER BY id").fetchall()
        return [RunRecord(**dict(row)) for row in rows]

    def register_candidate(
        self,
        run_id: int,
        summary: str,
        *,
        branch: str = "",
        base_commit: str = "",
        head_commit: str = "",
        patch_path: str = "",
        status: str = "registered",
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO candidates(
                run_id, summary, branch, base_commit, head_commit, patch_path, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, summary, branch, base_commit, head_commit, patch_path, status, utc_now()),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def list_candidates(self, run_id: int) -> List[CandidateRecord]:
        rows = self.connection.execute(
            "SELECT * FROM candidates WHERE run_id = ? ORDER BY id", (run_id,)
        ).fetchall()
        return [CandidateRecord(**dict(row)) for row in rows]

    def get_candidate(self, candidate_id: int) -> Optional[CandidateRecord]:
        row = self.connection.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if row is None:
            return None
        return CandidateRecord(**dict(row))

    def attach_candidate_patch(
        self,
        candidate_id: int,
        *,
        patch_path: str,
        head_commit: str = "",
        status: str | None = None,
    ) -> None:
        candidate = self.get_candidate(candidate_id)
        if candidate is None:
            raise KeyError(f"Candidate {candidate_id} was not found.")
        new_status = status if status is not None else candidate.status
        self.connection.execute(
            "UPDATE candidates SET patch_path = ?, head_commit = ?, status = ? WHERE id = ?",
            (patch_path, head_commit, new_status, candidate_id),
        )
        self.connection.commit()

    def record_evaluation(
        self,
        candidate_id: int,
        evaluation_type: str,
        status: str,
        *,
        command: str = "",
        score: float | None = None,
        logs_path: str = "",
        failure_reason: str = "",
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO evaluations(
                candidate_id, type, command, status, score, logs_path, failure_reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (candidate_id, evaluation_type, command, status, score, logs_path, failure_reason, utc_now()),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def record_decision(
        self,
        run_id: int,
        decision_type: str,
        *,
        candidate_id: int | None = None,
        rationale: str = "",
        actor: str = "",
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO decisions(run_id, candidate_id, decision_type, rationale, actor, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, candidate_id, decision_type, rationale, actor, utc_now()),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def list_evaluations_for_candidates(self, candidate_ids: Iterable[int]) -> List[sqlite3.Row]:
        ids = list(candidate_ids)
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        return self.connection.execute(
            f"SELECT * FROM evaluations WHERE candidate_id IN ({placeholders}) ORDER BY id", ids
        ).fetchall()

    def record_cost(
        self,
        *,
        run_id: int | None = None,
        candidate_id: int | None = None,
        agent: str = "",
        model: str = "",
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        tool_calls: int | None = None,
        wall_clock_seconds: float | None = None,
        estimated_usd: float | None = None,
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO costs(
                run_id, candidate_id, agent, model, input_tokens, output_tokens,
                tool_calls, wall_clock_seconds, estimated_usd, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                candidate_id,
                agent,
                model,
                input_tokens,
                output_tokens,
                tool_calls,
                wall_clock_seconds,
                estimated_usd,
                utc_now(),
            ),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def record_lineage(
        self,
        candidate_id: int,
        relationship: str,
        *,
        related_candidate_id: int | None = None,
        note: str = "",
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO candidate_lineage(
                candidate_id, relationship, related_candidate_id, note, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (candidate_id, relationship, related_candidate_id, note, utc_now()),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def list_lineage(self, run_id: int) -> List[LineageRecord]:
        rows = self.connection.execute(
            """
            SELECT candidate_lineage.*
            FROM candidate_lineage
            JOIN candidates ON candidates.id = candidate_lineage.candidate_id
            WHERE candidates.run_id = ?
            ORDER BY candidate_lineage.id
            """,
            (run_id,),
        ).fetchall()
        return [LineageRecord(**dict(row)) for row in rows]

    def list_costs(self, run_id: int) -> List[CostRecord]:
        rows = self.connection.execute(
            "SELECT * FROM costs WHERE run_id = ? OR candidate_id IN "
            "(SELECT id FROM candidates WHERE run_id = ?) ORDER BY id",
            (run_id, run_id),
        ).fetchall()
        return [CostRecord(**dict(row)) for row in rows]

    def list_decisions(self, run_id: int) -> List[DecisionRecord]:
        rows = self.connection.execute(
            "SELECT * FROM decisions WHERE run_id = ? ORDER BY id", (run_id,)
        ).fetchall()
        return [DecisionRecord(**dict(row)) for row in rows]

    def record_report(
        self, run_id: int, path: Path, *, summary: str = "", recommendation: str = ""
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO reports(run_id, path, format, summary, recommendation, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, str(path), "markdown", summary, recommendation, utc_now()),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def list_issue_proposals(self) -> List[IssueProposalRecord]:
        rows = self.connection.execute("SELECT * FROM issue_proposals ORDER BY id").fetchall()
        return [IssueProposalRecord(**dict(row)) for row in rows]

    def compare_candidates(self, run_id: int) -> List[dict]:
        candidates = self.list_candidates(run_id)
        evaluations = self.list_evaluations_for_candidates(candidate.id for candidate in candidates)
        failures: dict[int, int] = {}
        passes: dict[int, int] = {}
        for evaluation in evaluations:
            candidate_id = int(evaluation["candidate_id"])
            if evaluation["status"] == "passed":
                passes[candidate_id] = passes.get(candidate_id, 0) + 1
            else:
                failures[candidate_id] = failures.get(candidate_id, 0) + 1
        ranked = sorted(
            candidates,
            key=lambda candidate: (
                failures.get(candidate.id, 0),
                -passes.get(candidate.id, 0),
                candidate.id,
            ),
        )
        return [
            {
                **candidate.__dict__,
                "passing_evaluations": passes.get(candidate.id, 0),
                "failing_evaluations": failures.get(candidate.id, 0),
            }
            for candidate in ranked
        ]

    def propose_issue(
        self,
        title: str,
        body: str,
        *,
        labels: str = "",
        priority: str = "",
        evidence: str = "",
        source_run_ids: str = "",
        source_candidate_ids: str = "",
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO issue_proposals(
                title, body, labels, priority, evidence, source_run_ids, source_candidate_ids, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (title, body, labels, priority, evidence, source_run_ids, source_candidate_ids, utc_now()),
        )
        self.connection.commit()
        return int(cursor.lastrowid)
