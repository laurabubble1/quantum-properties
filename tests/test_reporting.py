from quantum_properties.reporting import HTMLReport, ReportFormatter, TestMetrics, TestReport


def test_test_report_summary_includes_failure_details():
    metrics = TestMetrics(total_tests=3, passed_tests=2, failed_tests=1, pass_rate=2 / 3, errors=["boom"])
    report = TestReport(circuit_name="bell", metrics=metrics)

    text = report.summary()
    assert "bell" in text
    assert "2/3 passed" in text
    assert "Failures: 1" in text
    assert "boom" in text


def test_test_report_detailed_report_includes_sections():
    metrics = TestMetrics(total_tests=2, passed_tests=2, failed_tests=0, pass_rate=1.0, errors=[])
    report = TestReport(
        circuit_name="ghz",
        metrics=metrics,
        property_results={"entangled": True},
        statistical_results={"entropy": 1.0},
        noise_results={"fidelity_loss": 0.1},
        statevector_results={"amp": True},
    )

    text = report.detailed_report()
    assert "TEST REPORT: ghz" in text
    assert "Property Tests:" in text
    assert "Statistical Analysis:" in text
    assert "Noise Robustness:" in text
    assert "State Vector Verification:" in text


def test_histogram_text_handles_empty_and_non_empty_distributions():
    assert ReportFormatter.histogram_text({}) == "No data"

    histogram = ReportFormatter.histogram_text({"0": 10, "1": 5}, max_width=10)
    assert "|0" in histogram
    assert "|1" in histogram
    assert "10" in histogram


def test_comparison_table_formats_rows_for_all_states():
    table = ReportFormatter.comparison_table({"0": 8, "1": 2}, {"0": 5, "1": 5})
    assert "State" in table
    assert "Difference" in table
    assert "|    0" in table
    assert "|    1" in table


def test_metrics_table_formats_mixed_values():
    table = ReportFormatter.metrics_table({"fidelity": 0.9, "status": "ok"})
    assert "fidelity" in table
    assert "0.900000" in table
    assert "status" in table
    assert "ok" in table


def test_pass_fail_summary_computes_rate_and_lists_results():
    summary = ReportFormatter.pass_fail_summary({"a": True, "b": False})
    assert "1/2 passed" in summary
    assert "PASS" in summary
    assert "FAIL" in summary


def test_html_report_includes_metrics_properties_and_errors():
    metrics = TestMetrics(total_tests=3, passed_tests=2, failed_tests=1, pass_rate=2 / 3, errors=["failure"])
    html = HTMLReport.generate_report(
        circuit_name="demo",
        metrics=metrics,
        property_results={"entangled": True, "balanced": False},
        distribution={"0": 1},
    )

    assert "Quantum Circuit Test Report" in html
    assert "demo" in html
    assert "entangled" in html
    assert "balanced" in html
    assert "failure" in html
