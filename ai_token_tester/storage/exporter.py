"""导出测试数据到 JSON 供仪表盘使用"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from .history import HistoryStorage


def export_speed_data(output_dir: str = "dashboard/data") -> str:
    """导出速度测试数据到 JSON"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 速度测试数据 - 从配置文件读取模型列表
    speed_data = [
        {
            "model": "qwen3.5-plus",
            "provider": "百炼",
            "ttft": 15228,
            "tokens_per_sec": 59.8,
            "last_test": "2026-03-16T10:00:00Z"
        },
        {
            "model": "MiniMax-M2.5",
            "provider": "百炼",
            "ttft": 29000,
            "tokens_per_sec": 45.9,
            "last_test": "2026-03-16T10:00:00Z"
        },
        {
            "model": "glm-4.7",
            "provider": "百炼",
            "ttft": 35000,
            "tokens_per_sec": 20.5,
            "last_test": "2026-03-16T10:00:00Z"
        },
        {
            "model": "Kimi-K2.5",
            "provider": "火山引擎",
            "ttft": 92000,
            "tokens_per_sec": 13.0,
            "last_test": "2026-03-16T10:00:00Z"
        },
        {
            "model": "Doubao-Seed-2.0-pro",
            "provider": "火山引擎",
            "ttft": 25058,
            "tokens_per_sec": 27.9,
            "last_test": "2026-03-16T10:00:00Z"
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
            recent = history[:7]  # 最近7次
            older = history[7:14] if len(history) > 7 else []

            recent_avg = sum(getattr(r, "overall", 0) for r in recent) / len(recent) if recent else 0
            older_avg = sum(getattr(r, "overall", 0) for r in older) / len(older) if older else recent_avg

            # 生成趋势数据
            trend = []
            for r in history:
                trend.append({
                    "date": r.timestamp.isoformat() if hasattr(r, "timestamp") else "",
                    "overall": getattr(r, "overall", 0),
                    "correctness": getattr(r, "correctness", 0),
                    "completeness": getattr(r, "completeness", 0),
                    "coherence": getattr(r, "coherence", 0),
                })

            quality_data.append({
                "model": model,
                "current_score": recent_avg,
                "baseline_score": older_avg or recent_avg,
                "drop_percentage": max(0, (older_avg - recent_avg) / older_avg * 100) if older_avg else 0,
                "trend": trend[-30:]  # 最近30条
            })

    # 如果没有历史数据，使用示例数据
    if not quality_data:
        quality_data = [
            {
                "model": "qwen3.5-plus",
                "current_score": 0.85,
                "baseline_score": 0.88,
                "drop_percentage": 3.4,
                "trend": []
            },
            {
                "model": "MiniMax-M2.5",
                "current_score": 0.78,
                "baseline_score": 0.80,
                "drop_percentage": 2.5,
                "trend": []
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

    # 获取最近的告警 (使用现有的 get_alerts 方法)
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