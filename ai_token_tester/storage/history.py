"""历史数据存储 - 使用SQLite存储质量评估历史"""

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class ModelScoreRecord:
    """模型分数记录"""
    id: int
    model: str
    provider: str
    test_key: str
    correctness: float
    completeness: float
    coherence: float
    overall: float
    run_time: datetime


class HistoryStorage:
    """历史数据存储"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # 默认存储在用户目录
            home_dir = Path.home() / ".ai_token_tester"
            home_dir.mkdir(exist_ok=True)
            db_path = str(home_dir / "quality_history.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建模型分数表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL,
                provider TEXT NOT NULL,
                test_key TEXT NOT NULL,
                correctness REAL NOT NULL,
                completeness REAL NOT NULL,
                coherence REAL NOT NULL,
                overall REAL NOT NULL,
                run_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建测试运行记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                providers TEXT,
                models TEXT,
                test_count INTEGER,
                status TEXT
            )
        """)

        # 创建降智告警表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL,
                metric TEXT NOT NULL,
                current_score REAL NOT NULL,
                baseline_score REAL NOT NULL,
                drop_percentage REAL NOT NULL,
                severity TEXT NOT NULL,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scores_model
            ON model_scores(model, run_time)
        """)

        conn.commit()
        conn.close()

    def save_result(
        self,
        model: str,
        provider: str,
        test_key: str,
        correctness: float,
        completeness: float,
        coherence: float,
        overall: float,
    ):
        """保存测试结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO model_scores
            (model, provider, test_key, correctness, completeness, coherence, overall)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (model, provider, test_key, correctness, completeness, coherence, overall),
        )

        conn.commit()
        conn.close()

    def get_history(
        self, model: str, days: int = 30, test_key: Optional[str] = None
    ) -> List[ModelScoreRecord]:
        """获取历史分数"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT id, model, provider, test_key, correctness, completeness,
                   coherence, overall, run_time
            FROM model_scores
            WHERE model = ?
            AND run_time >= datetime('now', '-' || ? || ' days')
        """
        params = [model, days]

        if test_key:
            query += " AND test_key = ?"
            params.append(test_key)

        query += " ORDER BY run_time DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [
            ModelScoreRecord(
                id=row["id"],
                model=row["model"],
                provider=row["provider"],
                test_key=row["test_key"],
                correctness=row["correctness"],
                completeness=row["completeness"],
                coherence=row["coherence"],
                overall=row["overall"],
                run_time=datetime.fromisoformat(row["run_time"]),
            )
            for row in rows
        ]

    def get_trend(
        self, model: str, metric: str = "overall", days: int = 30
    ) -> List[Tuple[datetime, float]]:
        """获取趋势数据"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 聚合每天的平均分数
        cursor.execute(
            """
            SELECT date(run_time) as day,
                   AVG(?) as score
            FROM model_scores
            WHERE model = ?
            AND run_time >= datetime('now', '-' || ? || ' days')
            GROUP BY date(run_time)
            ORDER BY day
            """,
            (metric, model, days),
        )

        rows = cursor.fetchall()
        conn.close()

        return [(datetime.strptime(row["day"], "%Y-%m-%d"), row["score"]) for row in rows]

    def get_baseline(
        self, model: str, metric: str = "overall", from_date: Optional[str] = None
    ) -> Optional[float]:
        """获取基准分数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if from_date:
            cursor.execute(
                f"""
                SELECT AVG({metric}) as baseline
                FROM model_scores
                WHERE model = ?
                AND run_time < ?
                """,
                (model, from_date),
            )
        else:
            # 默认取最近30天之前的数据作为基准
            cursor.execute(
                """
                SELECT AVG(overall) as baseline
                FROM model_scores
                WHERE model = ?
                AND run_time < datetime('now', '-30 days')
                """,
                (model,),
            )

        row = cursor.fetchone()
        conn.close()

        return row["baseline"] if row and row["baseline"] else None

    def save_alert(
        self,
        model: str,
        metric: str,
        current_score: float,
        baseline_score: float,
        drop_percentage: float,
        severity: str,
        message: str,
    ):
        """保存告警"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO alerts
            (model, metric, current_score, baseline_score, drop_percentage, severity, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (model, metric, current_score, baseline_score, drop_percentage, severity, message),
        )

        conn.commit()
        conn.close()

    def get_alerts(
        self, model: Optional[str] = None, days: int = 7
    ) -> List[dict]:
        """获取告警记录"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT * FROM alerts
            WHERE created_at >= datetime('now', '-' || ? || ' days')
        """
        params = [days]

        if model:
            query += " AND model = ?"
            params.append(model)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_all_models(self) -> List[str]:
        """获取所有测试过的模型"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT model FROM model_scores ORDER BY model
        """)

        rows = cursor.fetchall()
        conn.close()

        return [row[0] for row in rows]