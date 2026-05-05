# tests/quality/test_benchmark.py
"""核心场景基准测试 — 防止退化"""
import pytest
import json
from pathlib import Path
from typing import Dict

_HERE = Path(__file__).parent
_SCENARIOS_PATH = _HERE / "benchmarks" / "scenarios.json"

if _SCENARIOS_PATH.exists():
    with open(_SCENARIOS_PATH) as f:
        SCENARIOS = json.load(f)
else:
    SCENARIOS = []


class TestBenchmarks:
    """对每个场景执行规则检查"""

    @pytest.mark.parametrize("scenario", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
    def test_no_forbidden_words_in_real_output(self, scenario):
        """真实输出中不应包含违禁词（仅检查当前已有的输出）"""
        from .test_rules import REAL_AI_OUTPUT_MARKET, REAL_AI_OUTPUT_NEGOTIATOR
        combined = REAL_AI_OUTPUT_MARKET + REAL_AI_OUTPUT_NEGOTIATOR
        for word in scenario.get("forbidden_words", []):
            assert word not in combined, f"场景 {scenario['id']} 发现违禁词: {word}"
