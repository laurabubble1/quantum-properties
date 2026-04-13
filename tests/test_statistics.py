import math

import pytest
from qiskit import QuantumCircuit

from quantum_properties.statistics import QuantumStatistics


class _FakeResult:
    def __init__(self, counts):
        self._counts = counts

    def get_counts(self):
        return self._counts


class _FakeJob:
    def __init__(self, counts):
        self._counts = counts

    def result(self):
        return _FakeResult(self._counts)


class _FakeSimulator:
    def __init__(self, counts):
        self._counts = counts

    def run(self, _circuit):
        return _FakeJob(self._counts)


def measured_2q_circuit() -> QuantumCircuit:
    circuit = QuantumCircuit(2, 2)
    circuit.measure([0, 1], [0, 1])
    return circuit


def test_chi_square_test_uniform_default_expected_distribution():
    stats = QuantumStatistics(shots=100)
    stats.simulator = _FakeSimulator({"00": 25, "01": 25, "10": 25, "11": 25})

    result = stats.chi_square_test(measured_2q_circuit())

    assert result.statistic == 0
    assert result.p_value == 0.05
    assert result.degrees_of_freedom == 3
    assert result.significant is False


def test_chi_square_test_significant_when_distribution_is_skewed():
    stats = QuantumStatistics(shots=100)
    stats.simulator = _FakeSimulator({"0": 90, "1": 10})

    circuit = QuantumCircuit(1, 1)
    circuit.measure(0, 0)
    result = stats.chi_square_test(circuit, expected_distribution={"0": 0.5, "1": 0.5})

    assert result.statistic > 3.841
    assert result.p_value == 0.01
    assert result.significant is True


def test_chi_square_test_requires_classical_bits():
    stats = QuantumStatistics(shots=100)

    with pytest.raises(ValueError):
        stats.chi_square_test(QuantumCircuit(1))


def test_qubit_correlation_calculates_correlation_and_mutual_information():
    stats = QuantumStatistics(shots=100)
    stats.simulator = _FakeSimulator({"00": 50, "11": 50})

    result = stats.qubit_correlation(measured_2q_circuit(), 0, 1)

    assert result.qubit_pair == (0, 1)
    assert math.isclose(result.correlation, 1.0, rel_tol=1e-9)
    assert result.mutual_information >= 0


def test_qubit_correlation_requires_classical_bits():
    stats = QuantumStatistics(shots=100)

    with pytest.raises(ValueError):
        stats.qubit_correlation(QuantumCircuit(2), 0, 1)


def test_entanglement_entropy_is_shannon_entropy_of_distribution():
    stats = QuantumStatistics(shots=100)
    stats.simulator = _FakeSimulator({"0": 50, "1": 50})

    circuit = QuantumCircuit(1, 1)
    circuit.measure(0, 0)
    entropy = stats.entanglement_entropy(circuit)

    assert math.isclose(entropy, 1.0, rel_tol=1e-9)


def test_distribution_fidelity_matches_reference_distribution():
    stats = QuantumStatistics(shots=100)
    stats.simulator = _FakeSimulator({"0": 25, "1": 75})

    circuit = QuantumCircuit(1, 1)
    circuit.measure(0, 0)
    fidelity = stats.distribution_fidelity(circuit, {"0": 0.25, "1": 0.75})

    assert math.isclose(fidelity, 1.0, rel_tol=1e-9)
