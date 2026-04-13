from qiskit import QuantumCircuit
import pytest

from quantum_properties.statevector import StateVectorVerifier


class _FakeArray:
    def __init__(self, values):
        self._values = values

    def tolist(self):
        return self._values


class _FakeStatevectorWithData:
    def __init__(self, values):
        self.data = _FakeArray(values)


class _FakeStatevectorNoData:
    def __init__(self, values):
        self._values = values

    def tolist(self):
        return self._values


class _FakeResult:
    def __init__(self, values, with_data=True):
        self._values = values
        self._with_data = with_data

    def get_statevector(self, _circuit):
        if self._with_data:
            return _FakeStatevectorWithData(self._values)
        return _FakeStatevectorNoData(self._values)


class _FakeJob:
    def __init__(self, values, with_data=True):
        self._result = _FakeResult(values, with_data)

    def result(self):
        return self._result


def test_get_statevector_strips_measurements_and_reset(monkeypatch):
    verifier = StateVectorVerifier()
    captured = {}

    def fake_run(circuit):
        captured["ops"] = [inst.operation.name for inst in circuit.data]
        return _FakeJob([1 + 0j, 0 + 0j])

    monkeypatch.setattr(verifier.simulator, "run", fake_run)

    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)
    circuit.reset(0)

    statevector = verifier.get_statevector(circuit)

    assert captured["ops"] == ["h"]
    assert statevector == [1 + 0j, 0 + 0j]


def test_get_statevector_supports_objects_without_data_attr(monkeypatch):
    verifier = StateVectorVerifier()
    monkeypatch.setattr(verifier.simulator, "run", lambda _c: _FakeJob([0 + 0j, 1 + 0j], with_data=False))

    circuit = QuantumCircuit(1)
    statevector = verifier.get_statevector(circuit)

    assert statevector == [0 + 0j, 1 + 0j]


def test_assert_amplitude_pass_and_fail(monkeypatch):
    verifier = StateVectorVerifier()
    monkeypatch.setattr(verifier, "get_statevector", lambda _c: [1 + 0j, 0 + 0j])

    circuit = QuantumCircuit(1)
    assert verifier.assert_amplitude(circuit, "0", 1 + 0j)

    with pytest.raises(AssertionError):
        verifier.assert_amplitude(circuit, "1", 1 + 0j)


def test_assert_amplitude_magnitude_pass_and_fail(monkeypatch):
    verifier = StateVectorVerifier()
    monkeypatch.setattr(verifier, "get_statevector", lambda _c: [0.6 + 0.8j, 0 + 0j])

    circuit = QuantumCircuit(1)
    assert verifier.assert_amplitude_magnitude(circuit, "0", 1.0, tolerance=1e-9)

    with pytest.raises(AssertionError):
        verifier.assert_amplitude_magnitude(circuit, "1", 1.0)
