from qiskit import QuantumCircuit
import pytest

import quantum_properties.core as core


def measured_2q_circuit() -> QuantumCircuit:
    circuit = QuantumCircuit(2, 2)
    circuit.measure([0, 1], [0, 1])
    return circuit


def test_assert_entangled_passes_with_sufficient_entropy():
    tester = core.QuantumPropertyTest(shots=100)
    tester.measure_distribution = lambda _c: {"00": 50, "11": 50}

    assert tester.assert_entangled(measured_2q_circuit(), [0, 1], entropy_threshold=0.5)


def test_assert_entangled_raises_without_classical_bits():
    tester = core.QuantumPropertyTest()
    circuit = QuantumCircuit(2)

    with pytest.raises(ValueError):
        tester.assert_entangled(circuit, [0, 1])


def test_assert_entangled_fails_when_entropy_too_low():
    tester = core.QuantumPropertyTest(shots=100)
    tester.measure_distribution = lambda _c: {"00": 100}

    with pytest.raises(AssertionError):
        tester.assert_entangled(measured_2q_circuit(), [0, 1], entropy_threshold=0.6)


def test_assert_separable_passes_with_low_entropy():
    tester = core.QuantumPropertyTest(shots=100)
    tester.measure_distribution = lambda _c: {"00": 100}

    assert tester.assert_separable(measured_2q_circuit(), [0, 1], entropy_threshold=0.3)


def test_assert_separable_fails_when_entropy_too_high():
    tester = core.QuantumPropertyTest(shots=100)
    tester.measure_distribution = lambda _c: {"00": 30, "01": 30, "10": 20, "11": 20}

    with pytest.raises(AssertionError):
        tester.assert_separable(measured_2q_circuit(), [0, 1], entropy_threshold=0.1)


def test_assert_most_frequent_checks_expected_state_and_frequency():
    tester = core.QuantumPropertyTest(shots=100)
    tester.measure_distribution = lambda _c: {"1": 90, "0": 10}
    circuit = QuantumCircuit(1, 1)
    circuit.measure(0, 0)

    assert tester.assert_most_frequent(circuit, expected_state="1", min_frequency=0.5)


def test_assert_most_frequent_raises_for_empty_distribution():
    tester = core.QuantumPropertyTest(shots=100)
    tester.measure_distribution = lambda _c: {}
    circuit = QuantumCircuit(1, 1)
    circuit.measure(0, 0)

    with pytest.raises(ValueError):
        tester.assert_most_frequent(circuit)


def test_assert_equal_superposition_passes_when_balanced():
    tester = core.QuantumPropertyTest(shots=100)
    tester.measure_distribution = lambda _c: {"0": 50, "1": 50}
    circuit = QuantumCircuit(1, 1)
    circuit.measure(0, 0)

    assert tester.assert_equal_superposition(circuit, max_deviation=0.05)


def test_assert_equal_superposition_fails_when_unbalanced():
    tester = core.QuantumPropertyTest(shots=100)
    tester.measure_distribution = lambda _c: {"0": 90, "1": 10}
    circuit = QuantumCircuit(1, 1)
    circuit.measure(0, 0)

    with pytest.raises(AssertionError):
        tester.assert_equal_superposition(circuit, max_deviation=0.1)


def test_assert_distribution_matches_passes():
    tester = core.QuantumPropertyTest(shots=100)
    tester.measure_distribution = lambda _c: {"0": 52, "1": 48}
    circuit = QuantumCircuit(1, 1)
    circuit.measure(0, 0)

    assert tester.assert_distribution_matches(circuit, {"0": 0.5, "1": 0.5}, tolerance=0.05)


def test_assert_distribution_matches_fails_on_large_deviation():
    tester = core.QuantumPropertyTest(shots=100)
    tester.measure_distribution = lambda _c: {"0": 80, "1": 20}
    circuit = QuantumCircuit(1, 1)
    circuit.measure(0, 0)

    with pytest.raises(AssertionError):
        tester.assert_distribution_matches(circuit, {"0": 0.5, "1": 0.5}, tolerance=0.1)


def test_functional_wrapper_assert_entangled_forwards_runs(monkeypatch):
    circuit = measured_2q_circuit()

    def fake_assert(self, _circuit, qubits):
        assert self.shots == 77
        assert qubits == [0, 1]
        return True

    monkeypatch.setattr(core.QuantumPropertyTest, "assert_entangled", fake_assert)

    assert core.assert_entangled(circuit, [0, 1], runs=77)


def test_functional_wrapper_assert_separable_forwards_runs(monkeypatch):
    circuit = measured_2q_circuit()

    def fake_assert(self, _circuit, qubits):
        assert self.shots == 55
        assert qubits == [0, 1]
        return True

    monkeypatch.setattr(core.QuantumPropertyTest, "assert_separable", fake_assert)

    assert core.assert_separable(circuit, [0, 1], runs=55)


def test_functional_wrapper_assert_most_frequent(monkeypatch):
    circuit = QuantumCircuit(1, 1)
    circuit.measure(0, 0)

    def fake_assert(self, _circuit, expected_state=None):
        assert self.shots == 90
        assert expected_state == "0"
        return True

    monkeypatch.setattr(core.QuantumPropertyTest, "assert_most_frequent", fake_assert)

    assert core.assert_most_frequent(circuit, expected_state="0", runs=90)


def test_functional_wrapper_assert_equal_superposition(monkeypatch):
    circuit = QuantumCircuit(1, 1)
    circuit.measure(0, 0)

    def fake_assert(self, _circuit, max_deviation=0.1):
        assert self.shots == 88
        assert max_deviation == 0.2
        return True

    monkeypatch.setattr(core.QuantumPropertyTest, "assert_equal_superposition", fake_assert)

    assert core.assert_equal_superposition(circuit, runs=88, max_deviation=0.2)


def test_functional_wrapper_assert_distribution_matches(monkeypatch):
    circuit = QuantumCircuit(1, 1)
    circuit.measure(0, 0)

    def fake_assert(self, _circuit, expected_distribution, tolerance=0.05):
        assert self.shots == 66
        assert expected_distribution == {"0": 1.0}
        assert tolerance == 0.15
        return True

    monkeypatch.setattr(core.QuantumPropertyTest, "assert_distribution_matches", fake_assert)

    assert core.assert_distribution_matches(circuit, {"0": 1.0}, runs=66, tolerance=0.15)
