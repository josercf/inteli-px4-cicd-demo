"""Testes unit para tools.quality_gates."""

import json
from pathlib import Path

from tools.quality_gates import (
    GateResult,
    check_coverage,
    check_mission_metrics,
    check_sonar,
    evaluate,
)


def _write_coverage_xml(path: Path, line_rate: float) -> Path:
    path.write_text(
        f'<?xml version="1.0" ?>\n'
        f'<coverage line-rate="{line_rate}" version="6.5">\n'
        f'  <packages><package name="libs"/></packages>\n'
        f"</coverage>\n"
    )
    return path


class TestCoverageGate:
    def test_passes_when_above_threshold(self, tmp_path: Path) -> None:
        xml = _write_coverage_xml(tmp_path / "cov.xml", 0.85)
        result = check_coverage(xml, threshold=0.80)
        assert result.passed
        assert result.actual == 0.85

    def test_fails_when_below_threshold(self, tmp_path: Path) -> None:
        xml = _write_coverage_xml(tmp_path / "cov.xml", 0.70)
        result = check_coverage(xml, threshold=0.80)
        assert not result.passed
        assert result.actual == 0.70

    def test_fails_when_file_missing(self, tmp_path: Path) -> None:
        result = check_coverage(tmp_path / "missing.xml", threshold=0.80)
        assert not result.passed
        assert "não encontrado" in result.message


class TestMissionMetricsGate:
    def _write_metrics(self, path: Path, **kw: float) -> Path:
        path.write_text(json.dumps(kw))
        return path

    def test_passes_when_all_within(self, tmp_path: Path) -> None:
        metrics = self._write_metrics(
            tmp_path / "m.json",
            max_acceleration_m_s2=10.0,
            mission_duration_s=120,
            std_altitude_cruise_m=0.3,
        )
        gates = {
            "max_acceleration_m_s2": 15.0,
            "max_mission_duration_s": 180,
            "min_altitude_stability_m": 0.5,
        }
        results = check_mission_metrics(metrics, gates)
        assert all(r.passed for r in results)

    def test_fails_on_acceleration_breach(self, tmp_path: Path) -> None:
        metrics = self._write_metrics(
            tmp_path / "m.json",
            max_acceleration_m_s2=20.0,
            mission_duration_s=100,
            std_altitude_cruise_m=0.3,
        )
        results = check_mission_metrics(
            metrics,
            {
                "max_acceleration_m_s2": 15.0,
                "max_mission_duration_s": 180,
                "min_altitude_stability_m": 0.5,
            },
        )
        breached = [r for r in results if "max_acceleration" in r.name]
        assert breached and not breached[0].passed

    def test_missing_metric_fails_explicitly(self, tmp_path: Path) -> None:
        metrics = self._write_metrics(tmp_path / "m.json", mission_duration_s=100)
        results = check_mission_metrics(metrics, {"max_acceleration_m_s2": 15.0})
        breached = [r for r in results if "max_acceleration" in r.name]
        assert breached and not breached[0].passed
        assert "ausente" in breached[0].message


class TestSonarGate:
    def test_skip_when_not_required(self) -> None:
        result = check_sonar(host_url=None, token=None, project_key=None, require=False)
        assert result.passed
        assert result.actual == "skipped"

    def test_fail_when_required_but_missing_params(self) -> None:
        result = check_sonar(host_url=None, token=None, project_key=None, require=True)
        assert not result.passed
        assert "ausentes" in result.message

    def test_fail_on_network_error(self) -> None:
        # Aponta pra host inexistente — deve cair em except, não em PASS acidental
        result = check_sonar(
            host_url="http://nonexistent.invalid",
            token="dummy",
            project_key="x",
            require=True,
        )
        assert not result.passed
        assert "erro" in result.message.lower()


class TestEvaluateOrchestration:
    def test_all_pass_returns_all_passed_true(self, tmp_path: Path) -> None:
        gates = tmp_path / "g.yaml"
        gates.write_text(
            """
coverage:
  min_line_coverage: 0.80
mission_metrics:
  max_acceleration_m_s2: 15.0
  max_mission_duration_s: 180
  min_altitude_stability_m: 0.5
sonar:
  require_quality_gate_passed: false
"""
        )
        _write_coverage_xml(tmp_path / "cov.xml", 0.90)
        metrics = tmp_path / "m.json"
        metrics.write_text(
            json.dumps(
                {
                    "max_acceleration_m_s2": 10.0,
                    "mission_duration_s": 100,
                    "std_altitude_cruise_m": 0.3,
                }
            )
        )
        report = evaluate(gates, metrics, tmp_path / "cov.xml", None, None, None)
        assert report.all_passed
        assert isinstance(report.results, list)
        assert isinstance(report.results[0], GateResult)

    def test_any_failure_marks_all_passed_false(self, tmp_path: Path) -> None:
        gates = tmp_path / "g.yaml"
        gates.write_text(
            "coverage:\n  min_line_coverage: 0.99\n"
            "mission_metrics: {}\n"
            "sonar:\n  require_quality_gate_passed: false\n"
        )
        _write_coverage_xml(tmp_path / "cov.xml", 0.50)
        report = evaluate(gates, tmp_path / "m.json", tmp_path / "cov.xml", None, None, None)
        assert not report.all_passed
