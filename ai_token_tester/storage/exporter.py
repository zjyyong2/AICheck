"""导出测试数据到 JSON 供仪表盘使用"""

import json
import os
from datetime import datetime
from pathlib import Path

from .history import HistoryStorage

# 测试结果存储文件
RESULTS_FILE = Path.home() / ".ai_token_tester" / "latest_results.json"


def load_latest_results():
    """从存储文件加载最新测试结果"""
    if RESULTS_FILE.exists():
        try:
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load results: {e}")
    return []


def export_speed_data(output_dir: str = "dashboard/data") -> str:
    """导出速度测试数据到 JSON"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 尝试从测试结果加载
    results = load_latest_results()

    if results:
        # 从实际测试结果生成
        speed_data = []
        for r in results:
            speed_data.append({
                "model": r.get("model", "Unknown"),
                "provider": r.get("provider", "Unknown"),
                "ttft": int(r.get("ttft_ms", 0)),
                "tokens_per_sec": float(r.get("tokens_per_second", 0)),
                "last_test": datetime.now().isoformat() + "Z"
            })
    else:
        # 使用示例数据
        speed_data = [
            {
                "model": "qwen3.5-plus",
                "provider": "Bailian",
                "ttft": 15228,
                "tokens_per_sec": 59.8,
                "last_test": datetime.now().isoformat() + "Z"
            },
            {
                "model": "MiniMax-M2.5",
                "provider": "Bailian",
                "ttft": 29000,
                "tokens_per_sec": 45.9,
                "last_test": datetime.now().isoformat() + "Z"
            },
            {
                "model": "glm-4.7",
                "provider": "Bailian",
                "ttft": 35000,
                "tokens_per_sec": 20.5,
                "last_test": datetime.now().isoformat() + "Z"
            },
            {
                "model": "Kimi-K2.5",
                "provider": "Volcengine",
                "ttft": 92000,
                "tokens_per_sec": 13.0,
                "last_test": datetime.now().isoformat() + "Z"
            },
            {
                "model": "Doubao-Seed-2.0-pro",
                "provider": "Volcengine",
                "ttft": 25058,
                "tokens_per_sec": 27.9,
                "last_test": datetime.now().isoformat() + "Z"
            }
        ]

    # 保存速度数据
    speed_file = output_path / "speed_data.json"
    with open(speed_file, "w", encoding="utf-8") as f:
        json.dump(speed_data, f, indent=2, ensure_ascii=False)

    return str(speed_file)


def export_quality_data(output_dir: str = "dashboard/data") -> str:
    """导出质量测试数据到 JSON"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    storage = HistoryStorage()

    # 获取所有模型的质量历史数据
    models = storage.get_all_models()

    quality_data = []
    for model in models:
        history = storage.get_history(model, days=30)
        if history:
            recent = history[:7]
            older = history[7:14] if len(history) > 7 else []

            recent_avg = sum(getattr(r, "overall", 0) for r in recent) / len(recent) if recent else 0
            older_avg = sum(getattr(r, "overall", 0) for r in older) / len(older) if older else recent_avg

            trend = []
            for r in history:
                trend.append({
                    "date": getattr(r, "run_time", "").strftime("%Y-%m-%d") if hasattr(r, "run_time") else "",
                    "overall": getattr(r, "overall", 0),
                    "correctness": getattr(r, "correctness", 0),
                    "completeness": getattr(r, "completeness", 0),
                    "coherence": getattr(r, "coherence", 0),
                })

            quality_data.append({
                "model": model,
                "provider": "Bailian",
                "current_score": recent_avg,
                "baseline_score": older_avg or recent_avg,
                "drop_percentage": max(0, (older_avg - recent_avg) / older_avg * 100) if older_avg else 0,
                "trend": trend[-30:]
            })

    # 如果没有历史数据，使用示例数据
    if not quality_data:
        quality_data = [
            {
                "model": "qwen3.5-plus",
                "provider": "Bailian",
                "current_score": 0.88,
                "baseline_score": 0.90,
                "drop_percentage": 2.2,
                "trend": [
                    {"date": "2026-03-10", "overall": 0.90},
                    {"date": "2026-03-11", "overall": 0.89},
                    {"date": "2026-03-12", "overall": 0.91},
                    {"date": "2026-03-13", "overall": 0.88},
                    {"date": "2026-03-14", "overall": 0.89},
                    {"date": "2026-03-15", "overall": 0.88},
                    {"date": "2026-03-16", "overall": 0.88}
                ]
            }
        ]

    # 保存质量数据
    quality_file = output_path / "quality_data.json"
    with open(quality_file, "w", encoding="utf-8") as f:
        json.dump(quality_data, f, indent=2, ensure_ascii=False)

    return str(quality_file)


def export_alerts_data(output_dir: str = "dashboard/data") -> str:
    """导出告警数据到 JSON"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    storage = HistoryStorage()

    # 获取最近的告警
    alerts_raw = storage.get_alerts(days=30)[:20]

    alerts_data = []
    for alert in alerts_raw:
        alerts_data.append({
            "id": alert.get("id", 0),
            "model": alert.get("model", ""),
            "metric": alert.get("metric", ""),
            "current_score": alert.get("current_score", 0),
            "baseline_score": alert.get("baseline_score", 0),
            "drop_percentage": alert.get("drop_percentage", 0),
            "severity": alert.get("severity", "warning"),
            "message": alert.get("message", ""),
            "timestamp": alert.get("created_at", "")
        })

    # 保存告警数据
    alerts_file = output_path / "alerts_data.json"
    with open(alerts_file, "w", encoding="utf-8") as f:
        json.dump(alerts_data, f, indent=2, ensure_ascii=False)

    return str(alerts_file)


def export_all_data(output_dir: str = "dashboard/data"):
    """导出所有数据"""
    files = []
    files.append(("speed", export_speed_data(output_dir)))
    files.append(("quality", export_quality_data(output_dir)))
    files.append(("alerts", export_alerts_data(output_dir)))

    return files


if __name__ == "__main__":
    import sys
    output = sys.argv[1] if len(sys.argv) > 1 else "dashboard/data"
    files = export_all_data(output)
    print("Exported data files:")
    for name, path in files:
        print(f"  {name}: {path}")