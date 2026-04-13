from qiskit import QuantumCircuit
import pytest

import quantum_properties.noise as noise
from quantum_properties.noise import NoiseImpactAnalysis, NoiseSimulator


class _FakeResult:
    def __init__(self, counts):
        self._counts = counts

    def get_counts(self, _circuit=None):
        return self._counts


class _FakeJob:
    def __init__(self, counts):
        self._counts = counts

    def result(self):
        return _FakeResult(self._counts)


def test_noise_profiles_have_expected_defaults():
    assert NoiseSimulator.DEFAULT_NOISE.single_qubit_error_rate > 0
    assert NoiseSimulator.LOW_NOISE.two_qubit_error_rate < NoiseSimulator.HIGH_NOISE.two_qubit_error_rate
    assert NoiseSimulator.HARDWARE_LIKE.amplitude_damping_rate > 0


def test_run_circuit_uses_noise_model_and_returns_counts(monkeypatch):
    simulator = NoiseSimulator(shots=123)
    marker_noise_model = object()
    monkeypatch.setattr(simulator, "_build_noise_model", lambda: marker_noise_model)

    captured = {}

    class _FakeAerSimulator:
        def __init__(self, noise_model=None, shots=None):
            captured["noise_model"] = noise_model
            captured["shots"] = shots

        def run(self, _circuit):
            return _FakeJob({"0": 100})

    monkeypatch.setattr(noise, "AerSimulator", _FakeAerSimulator)

    circuit = QuantumCircuit(1, 1)
    circuit.measure(0, 0)
    counts = simulator.run_circuit(circuit)

    assert counts == {"0": 100}
    assert captured["noise_model"] is marker_noise_model
    assert captured["shots"] == 123


def test_run_circuit_clean_uses_ideal_simulator(monkeypatch):
    simulator = NoiseSimulator(shots=200)
    captured = {}

    class _FakeAerSimulator:
        def __init__(self, shots=None):
            captured["shots"] = shots

        def run(self, _circuit):
            return _FakeJob({"1": 200})

    monkeypatch.setattr(noise, "AerSimulator", _FakeAerSimulator)

    circuit = QuantumCircuit(1, 1)
    circuit.measure(0, 0)
    counts = simulator.run_circuit_clean(circuit)

    assert counts == {"1": 200}
    assert captured["shots"] == 200


def test_compare_with_ideal_computes_loss_and_error_increase(monkeypatch):
    simulator = NoiseSimulator(shots=100)
    monkeypatch.setattr(simulator, "run_circuit_clean", lambda _c: {"00": 100})
    monkeypatch.setattr(simulator, "run_circuit", lambda _c: {"00": 80, "01": 20})

    circuit = QuantumCircuit(2, 2)
    circuit.name = "demo"
    analysis = simulator.compare_with_ideal(circuit)

    assert isinstance(analysis, NoiseImpactAnalysis)
    assert analysis.circuit_name == "demo"
    assert analysis.clean_distribution == {"00": 100}
    assert analysis.noisy_distribution == {"00": 80, "01": 20}
    assert analysis.fidelity_loss > 0
    assert analysis.error_rate_increase >= 0


def test_assert_noise_robust_pass_and_fail(monkeypatch):
    simulator = NoiseSimulator()

    monkeypatch.setattr(
        simulator,
        "compare_with_ideal",
        lambda _c: NoiseImpactAnalysis("c", {"0": 1}, {"0": 1}, 0.05, 0.0),
    )
    assert simulator.assert_noise_robust(QuantumCircuit(1), max_fidelity_loss=0.1)

    monkeypatch.setattr(
        simulator,
        "compare_with_ideal",
        lambda _c: NoiseImpactAnalysis("c", {"0": 1}, {"0": 1}, 0.2, 0.0),
    )
    with pytest.raises(AssertionError):
        simulator.assert_noise_robust(QuantumCircuit(1), max_fidelity_loss=0.1)


def test_assert_error_contained_pass_and_fail(monkeypatch):
    simulator = NoiseSimulator()

    monkeypatch.setattr(
        simulator,
        "compare_with_ideal",
        lambda _c: NoiseImpactAnalysis("c", {"0": 1}, {"0": 1}, 0.0, 0.01),
    )
    assert simulator.assert_error_contained(QuantumCircuit(1), max_error_increase=0.05)

    monkeypatch.setattr(
        simulator,
        "compare_with_ideal",
        lambda _c: NoiseImpactAnalysis("c", {"0": 1}, {"0": 1}, 0.0, 0.2),
    )
    with pytest.raises(AssertionError):
        simulator.assert_error_contained(QuantumCircuit(1), max_error_increase=0.05)


def test_test_under_noise_adds_measurement_and_handles_assertions(monkeypatch):
    simulator = NoiseSimulator(shots=10)
    monkeypatch.setattr(simulator, "run_circuit", lambda _c: {"0": 10})

    circuit = QuantumCircuit(1)
    result = simulator.test_under_noise(circuit, lambda counts: counts == {"0": 10})
    assert result is True

    result_fail = simulator.test_under_noise(circuit, lambda _counts: (_ for _ in ()).throw(AssertionError("no")))
    assert result_fail is False
