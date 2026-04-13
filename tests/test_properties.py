from qiskit import QuantumCircuit

from quantum_properties.properties import PropertyBuilder, PropertyResult, QuantumProperty


def test_property_result_str_formats_pass_and_fail():
    assert "PASS" in str(PropertyResult(name="ok", passed=True))
    assert "FAIL" in str(PropertyResult(name="bad", passed=False, error="oops"))


def test_quantum_property_decorator_success_path():
    prop = QuantumProperty(name="demo", runs=12)

    @prop
    def check(_circuit, runs):
        assert runs == 12
        return True

    circuit = QuantumCircuit(1, 1)
    result = check(circuit)

    assert isinstance(result, PropertyResult)
    assert result.name == "demo"
    assert result.passed is True


def test_quantum_property_decorator_handles_assertion_error():
    prop = QuantumProperty(name="must_fail")

    @prop
    def check(_circuit, _runs):
        raise AssertionError("failed")

    result = check(QuantumCircuit(1, 1))
    assert result.passed is False
    assert "failed" in (result.error or "")


def test_quantum_property_decorator_handles_generic_exception():
    prop = QuantumProperty(name="error_case")

    @prop
    def check(_circuit, _runs):
        raise RuntimeError("boom")

    result = check(QuantumCircuit(1, 1))
    assert result.passed is False
    assert "boom" in (result.error or "")


def test_property_builder_define_registers_property_and_executes():
    builder = PropertyBuilder(shots=10)

    @builder.define("is_true")
    def prop(_circuit):
        return True

    assert "is_true" in builder.properties
    result = prop(QuantumCircuit(1, 1))
    assert result.passed is True


def test_property_builder_define_supports_stats_dict():
    builder = PropertyBuilder()

    @builder.define("stats")
    def prop(_circuit):
        return {"value": 1}

    result = prop(QuantumCircuit(1, 1))
    assert result.passed is True
    assert result.stats == {"value": 1}


def test_property_builder_assert_helpers_delegate_to_tester(monkeypatch):
    builder = PropertyBuilder(shots=111)
    circuit = QuantumCircuit(2, 2)

    monkeypatch.setattr(builder.tester, "assert_entangled", lambda c, q: c is circuit and q == [0, 1])
    monkeypatch.setattr(builder.tester, "assert_separable", lambda c, q: c is circuit and q == [0, 1])
    monkeypatch.setattr(builder.tester, "assert_most_frequent", lambda c, e, m: c is circuit and e == "0" and m == 0.9)
    monkeypatch.setattr(builder.tester, "assert_equal_superposition", lambda c, d: c is circuit and d == 0.2)
    monkeypatch.setattr(builder.tester, "assert_distribution_matches", lambda c, d, t: c is circuit and d == {"00": 1.0} and t == 0.2)

    assert builder.assert_entangled(circuit, [0, 1])
    assert builder.assert_separable(circuit, [0, 1])
    assert builder.assert_most_frequent(circuit, "0", 0.9)
    assert builder.assert_equal_superposition(circuit, 0.2)
    assert builder.assert_distribution_matches(circuit, {"00": 1.0}, 0.2)


def test_test_circuit_collects_results_for_all_property_outcomes():
    builder = PropertyBuilder()

    builder.properties["returns_result"] = lambda _c: PropertyResult(name="returns_result", passed=True)
    builder.properties["returns_bool"] = lambda _c: True
    builder.properties["returns_dict_passed"] = lambda _c: {"passed": True}

    def _boom(_c):
        raise RuntimeError("failure")

    builder.properties["raises"] = _boom

    results = builder.test_circuit(QuantumCircuit(1, 1))
    by_name = {r.name: r for r in results}

    assert by_name["returns_result"].passed is True
    assert by_name["returns_bool"].passed is True
    assert by_name["returns_dict_passed"].passed is True
    assert by_name["raises"].passed is False
    assert "failure" in (by_name["raises"].error or "")


def test_test_batch_runs_all_circuits():
    builder = PropertyBuilder()
    builder.properties["always_true"] = lambda _c: True

    circuits = {"a": QuantumCircuit(1, 1), "b": QuantumCircuit(2, 2)}
    result = builder.test_batch(circuits)

    assert set(result.keys()) == {"a", "b"}
    assert all(len(v) == 1 for v in result.values())


def test_report_formats_summary():
    builder = PropertyBuilder()
    results = [
        PropertyResult(name="p1", passed=True),
        PropertyResult(name="p2", passed=False, error="no"),
    ]

    report = builder.report(results)

    assert "1/2 passed" in report
    assert "p1" in report
    assert "p2" in report
