"""Reporting and visualization for quantum circuit tests."""

from __future__ import annotations

from typing import NamedTuple
from dataclasses import dataclass


class CircuitMetrics(NamedTuple):
    """Test metrics and statistics."""
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate: float
    errors: list[str]


@dataclass
class CircuitReport:
    """Comprehensive test report for quantum circuits."""
    circuit_name: str
    metrics: CircuitMetrics
    property_results: dict[str, bool] | None = None
    statistical_results: dict[str, float] | None = None
    noise_results: dict[str, float] | None = None
    statevector_results: dict[str, bool] | None = None
    
    def summary(self) -> str:
        """Generate text summary.
        
        Returns:
            Formatted summary string
        """
        lines = [
            f"Circuit: {self.circuit_name}",
            f"Results: {self.metrics.passed_tests}/{self.metrics.total_tests} passed ({self.metrics.pass_rate:.1%})",
        ]
        
        if self.metrics.failed_tests > 0:
            lines.append(f"Failures: {self.metrics.failed_tests}")
            for error in self.metrics.errors:
                lines.append(f"  - {error}")
        
        return "\n".join(lines)
    
    def detailed_report(self) -> str:
        """Generate detailed report with all results.
        
        Returns:
            Formatted detailed report
        """
        parts = [
            "=" * 60,
            f"TEST REPORT: {self.circuit_name}",
            "=" * 60,
            "",
            self.summary(),
            "",
        ]
        
        if self.property_results:
            parts.append("Property Tests:")
            for name, passed in self.property_results.items():
                status = "✓ PASS" if passed else "✗ FAIL"
                parts.append(f"  {status}: {name}")
            parts.append("")
        
        if self.statistical_results:
            parts.append("Statistical Analysis:")
            for name, value in self.statistical_results.items():
                parts.append(f"  {name}: {value:.4f}")
            parts.append("")
        
        if self.noise_results:
            parts.append("Noise Robustness:")
            for name, value in self.noise_results.items():
                if isinstance(value, float) and 0 <= value <= 1:
                    parts.append(f"  {name}: {value:.2%}")
                else:
                    parts.append(f"  {name}: {value}")
            parts.append("")
        
        if self.statevector_results:
            parts.append("State Vector Verification:")
            for name, passed in self.statevector_results.items():
                status = "✓ PASS" if passed else "✗ FAIL"
                parts.append(f"  {status}: {name}")
            parts.append("")
        
        parts.append("=" * 60)
        
        return "\n".join(parts)


class ReportFormatter:
    """Format and display test results."""
    
    @staticmethod
    def histogram_text(distribution: dict[str, int], max_width: int = 40) -> str:
        """Create text-based histogram of distribution.
        
        Args:
            distribution: Measurement results as count dict
            max_width: Maximum width of histogram bars
            
        Returns:
            Formatted histogram string
        """
        if not distribution:
            return "No data"
        
        total = sum(distribution.values())
        max_count = max(distribution.values())
        
        lines = []
        for state, count in sorted(distribution.items()):
            prob = count / total
            bar_width = int((count / max_count) * max_width)
            bar = "█" * bar_width
            lines.append(f"|{state}⟩: {bar} {count:4d} ({prob:6.2%})")
        
        return "\n".join(lines)
    
    @staticmethod
    def comparison_table(
        ideal: dict[str, int],
        actual: dict[str, int],
    ) -> str:
        """Create comparison table between ideal and actual.
        
        Args:
            ideal: Ideal measurement distribution
            actual: Actual measurement distribution
            
        Returns:
            Formatted comparison table
        """
        ideal_total = sum(ideal.values())
        actual_total = sum(actual.values())
        
        all_states = sorted(set(ideal.keys()) | set(actual.keys()))
        
        lines = [
            "State    | Ideal    | Actual   | Difference",
            "---------|----------|----------|----------",
        ]
        
        for state in all_states:
            ideal_prob = (ideal.get(state, 0) / ideal_total) * 100
            actual_prob = (actual.get(state, 0) / actual_total) * 100
            diff = actual_prob - ideal_prob
            
            lines.append(
                f"|{state:>5}⟩  | {ideal_prob:6.2f}% | {actual_prob:6.2f}% | {diff:+6.2f}%"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def metrics_table(metrics: dict[str, float]) -> str:
        """Create metrics summary table.
        
        Args:
            metrics: Dictionary of metric names to values
            
        Returns:
            Formatted metrics table
        """
        lines = [
            "Metric Name          | Value",
            "---------------------|-----------",
        ]
        
        for name, value in metrics.items():
            if isinstance(value, float):
                lines.append(f"{name:20s} | {value:10.6f}")
            else:
                lines.append(f"{name:20s} | {value}")
        
        return "\n".join(lines)
    
    @staticmethod
    def pass_fail_summary(results: dict[str, bool]) -> str:
        """Create pass/fail summary.
        
        Args:
            results: Dictionary mapping test names to pass/fail
            
        Returns:
            Formatted summary
        """
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        lines = [f"Summary: {passed}/{total} passed ({100*passed/total:.1f}%)", ""]
        
        for name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            lines.append(f"  {status}: {name}")
        
        return "\n".join(lines)


class HTMLReport:
    """Generate HTML reports for quantum tests."""
    
    @staticmethod
    def generate_report(
        circuit_name: str,
        metrics: CircuitMetrics,
        property_results: dict[str, bool] | None = None,
        distribution: dict[str, int] | None = None,
    ) -> str:
        """Generate HTML report.
        
        Args:
            circuit_name: Name of tested circuit
            metrics: Circuit metrics
            property_results: Property test results
            distribution: Measurement distribution
            
        Returns:
            HTML report as string
        """
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Quantum Test Report - {circuit_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; }}
        .summary {{ background-color: #e3f2fd; padding: 10px; margin: 10px 0; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f0f0f0; }}
        .pass-rate {{ font-size: 24px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Quantum Circuit Test Report</h1>
        <h2>{circuit_name}</h2>
    </div>
    
    <div class="summary">
        <h3>Summary</h3>
        <p><strong>Total Tests:</strong> {metrics.total_tests}</p>
        <p><strong>Passed:</strong> <span class="pass">{metrics.passed_tests}</span></p>
        <p><strong>Failed:</strong> <span class="fail">{metrics.failed_tests}</span></p>
        <p class="pass-rate">
            Pass Rate: <span class="{'pass' if metrics.pass_rate > 0.8 else 'fail'}">
            {metrics.pass_rate:.1%}</span>
        </p>
    </div>
"""
        
        if property_results:
            html += """
    <h3>Property Test Results</h3>
    <table>
        <tr>
            <th>Property</th>
            <th>Result</th>
        </tr>
"""
            for name, passed in property_results.items():
                status = '<span class="pass">✓ PASS</span>' if passed else '<span class="fail">✗ FAIL</span>'
                html += f"""
        <tr>
            <td>{name}</td>
            <td>{status}</td>
        </tr>
"""
            html += "    </table>\n"
        
        if metrics.errors:
            html += """
    <h3>Errors</h3>
    <ul>
"""
            for error in metrics.errors:
                html += f"        <li>{error}</li>\n"
            html += "    </ul>\n"
        
        html += """
</body>
</html>
"""
        return html
