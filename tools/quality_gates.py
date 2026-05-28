"""CLI: avalia quality gates contra metrics.json, coverage.xml e Sonar API.

Saída: exit code 0 se todos os gates passam, != 0 se qualquer um falha.
Imprime relatório legível pro humano + estrutura JSON pro próximo passo do CI.

Uso:
    python -m tools.quality_gates \\
        --metrics reports/metrics.json \\
        --coverage coverage.xml \\
        --gates quality_gates.yaml \\
        [--sonar-host URL] [--sonar-token TOKEN] [--sonar-project-key KEY] \\
        [--output reports/quality_gates_result.json]

PR #4 (Aula 10) liga esse CLI no ci.yml como step `quality-gates` —
falha o pipeline e bloqueia merge se algum gate vermelho.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

LOG = logging.getLogger("quality_gates")


@dataclass
class GateResult:
    name: str
    passed: bool
    actual: float | str | None
    threshold: float | str | None
    message: str


@dataclass
class GatesReport:
    all_passed: bool
    results: list[GateResult] = field(default_factory=list)
    summary: str = ""


# --------------------------------------------------------------------------- #
# Coverage gate
# --------------------------------------------------------------------------- #


def _parse_coverage_xml(path: Path) -> float:
    """Lê coverage.xml (formato Cobertura) e retorna line-rate (0.0-1.0)."""
    tree = ET.parse(path)
    root = tree.getroot()
    line_rate = root.attrib.get("line-rate")
    if line_rate is None:
        raise ValueError(f"coverage.xml sem atributo line-rate: {path}")
    return float(line_rate)


def check_coverage(coverage_xml: Path, threshold: float) -> GateResult:
    if not coverage_xml.is_file():
        return GateResult(
            name="coverage.min_line_coverage",
            passed=False,
            actual=None,
            threshold=threshold,
            message=f"coverage.xml não encontrado: {coverage_xml}",
        )
    actual = _parse_coverage_xml(coverage_xml)
    passed = actual >= threshold
    return GateResult(
        name="coverage.min_line_coverage",
        passed=passed,
        actual=round(actual, 4),
        threshold=threshold,
        message=(f"line coverage {actual:.2%} {'≥' if passed else '<'} threshold {threshold:.0%}"),
    )


# --------------------------------------------------------------------------- #
# Mission metrics gates
# --------------------------------------------------------------------------- #


_METRIC_RULES = [
    # (gate_name, metric_key, comparison, message_template)
    ("mission_metrics.max_acceleration_m_s2", "max_acceleration_m_s2", "le", "≤"),
    ("mission_metrics.max_mission_duration_s", "mission_duration_s", "le", "≤"),
    ("mission_metrics.min_altitude_stability_m", "std_altitude_cruise_m", "le", "≤"),
]


def check_mission_metrics(metrics_json: Path, gates: dict[str, float]) -> list[GateResult]:
    results: list[GateResult] = []

    if not metrics_json.is_file():
        return [
            GateResult(
                name="mission_metrics",
                passed=False,
                actual=None,
                threshold=None,
                message=f"metrics.json não encontrado: {metrics_json}",
            )
        ]

    metrics = json.loads(metrics_json.read_text())

    for gate_name, metric_key, _comparison, op_symbol in _METRIC_RULES:
        threshold_key = gate_name.split(".", 1)[1]
        threshold = gates.get(threshold_key)
        if threshold is None:
            continue
        actual = metrics.get(metric_key)
        if actual is None:
            results.append(
                GateResult(
                    name=gate_name,
                    passed=False,
                    actual=None,
                    threshold=threshold,
                    message=f"métrica '{metric_key}' ausente em metrics.json",
                )
            )
            continue
        passed = float(actual) <= float(threshold)
        results.append(
            GateResult(
                name=gate_name,
                passed=passed,
                actual=actual,
                threshold=threshold,
                message=(
                    f"{metric_key} = {actual} {op_symbol if passed else '>'} threshold {threshold}"
                ),
            )
        )

    return results


# --------------------------------------------------------------------------- #
# Sonar gate — consulta API GET /api/qualitygates/project_status
# --------------------------------------------------------------------------- #


def _http_get_json(url: str, token: str | None) -> Any:
    req = urllib.request.Request(url)
    if token:
        # Sonar usa basic auth com token como username; password vazia.
        import base64

        auth = base64.b64encode(f"{token}:".encode()).decode()
        req.add_header("Authorization", f"Basic {auth}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def check_sonar(
    host_url: str | None, token: str | None, project_key: str | None, require: bool
) -> GateResult:
    if not require:
        return GateResult(
            name="sonar.require_quality_gate_passed",
            passed=True,
            actual="skipped",
            threshold="not required",
            message="sonar gate desativado em quality_gates.yaml",
        )
    if not (host_url and token and project_key):
        return GateResult(
            name="sonar.require_quality_gate_passed",
            passed=False,
            actual=None,
            threshold="PASSED",
            message="parâmetros do Sonar ausentes (host/token/project_key)",
        )
    try:
        url = f"{host_url.rstrip('/')}/api/qualitygates/project_status?" + urllib.parse.urlencode(
            {"projectKey": project_key}
        )
        data = _http_get_json(url, token)
        status = data.get("projectStatus", {}).get("status", "UNKNOWN")
        passed = status == "OK"
        return GateResult(
            name="sonar.require_quality_gate_passed",
            passed=passed,
            actual=status,
            threshold="OK",
            message=f"Sonar Quality Gate status = {status}",
        )
    except Exception as e:
        return GateResult(
            name="sonar.require_quality_gate_passed",
            passed=False,
            actual=None,
            threshold="OK",
            message=f"erro consultando Sonar: {e}",
        )


# --------------------------------------------------------------------------- #
# Orquestração
# --------------------------------------------------------------------------- #


def evaluate(
    gates_yaml: Path,
    metrics_json: Path,
    coverage_xml: Path,
    sonar_host: str | None,
    sonar_token: str | None,
    sonar_project_key: str | None,
) -> GatesReport:
    config = yaml.safe_load(gates_yaml.read_text())
    results: list[GateResult] = []

    # Coverage
    cov_threshold = config.get("coverage", {}).get("min_line_coverage")
    if cov_threshold is not None:
        results.append(check_coverage(coverage_xml, cov_threshold))

    # Mission metrics
    metrics_config = config.get("mission_metrics", {})
    if metrics_config:
        results.extend(check_mission_metrics(metrics_json, metrics_config))

    # Sonar
    sonar_config = config.get("sonar", {})
    results.append(
        check_sonar(
            sonar_host,
            sonar_token,
            sonar_project_key,
            require=sonar_config.get("require_quality_gate_passed", False),
        )
    )

    all_passed = all(r.passed for r in results)
    passed_count = sum(1 for r in results if r.passed)
    summary = f"{passed_count}/{len(results)} gates passaram"
    return GatesReport(all_passed=all_passed, results=results, summary=summary)


def _format_report(report: GatesReport) -> str:
    lines = [f"## Quality Gates: {report.summary}", ""]
    for r in report.results:
        emoji = "✅" if r.passed else "❌"
        lines.append(f"- {emoji} **{r.name}** — {r.message}")
    lines.append("")
    lines.append("**TODOS OS GATES PASSARAM** ✅" if report.all_passed else "**GATES FALHARAM** ❌")
    return "\n".join(lines)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s"
    )
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--gates", required=True, type=Path)
    p.add_argument("--metrics", required=True, type=Path)
    p.add_argument("--coverage", required=True, type=Path)
    p.add_argument("--sonar-host", default=os.environ.get("SONAR_HOST_URL"))
    p.add_argument("--sonar-token", default=os.environ.get("SONAR_TOKEN"))
    p.add_argument("--sonar-project-key", default=os.environ.get("SONAR_PROJECT_KEY"))
    p.add_argument("--output", type=Path, help="path pra JSON estruturado opcional")
    args = p.parse_args()

    report = evaluate(
        args.gates,
        args.metrics,
        args.coverage,
        args.sonar_host,
        args.sonar_token,
        args.sonar_project_key,
    )

    print(_format_report(report))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(
                {
                    "all_passed": report.all_passed,
                    "summary": report.summary,
                    "results": [asdict(r) for r in report.results],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    sys.exit(0 if report.all_passed else 1)


if __name__ == "__main__":
    main()
