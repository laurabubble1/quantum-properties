"""State vector verification for quantum circuits."""

from __future__ import annotations

import math
import cmath
from typing import NamedTuple

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


class AmplitudeComparison(NamedTuple):
    """Comparison of circuit and reference amplitudes."""
    basis_state: str
    circuit_amplitude: complex
    reference_amplitude: complex
    fidelity: float


class StateVectorVerifier:
    """Verify quantum circuits using exact state vectors."""
    
    def __init__(self):
        """Initialize state vector verifier."""
        self.simulator = AerSimulator(method='statevector')
    
    def get_statevector(self, circuit: QuantumCircuit) -> list[complex]:
        """Get exact statevector for circuit."""
        qc_copy = circuit.copy()
        
        # Remove measurements if present
        if hasattr(qc_copy, 'data'):
            qc_copy.data = [instr for instr in qc_copy.data 
                           if instr[0].name not in ['measure', 'reset']]
        
        result = self.simulator.run(qc_copy).result()
        sv = result.get_statevector(qc_copy)
        if hasattr(sv, 'data'):
            return sv.data.tolist()
        return sv.tolist()
    
    def assert_amplitude(self, circuit: QuantumCircuit, basis_state: str,
                        expected_amplitude: complex | float, tolerance: float = 1e-5) -> bool:
        statevector = self.get_statevector(circuit)
        index = int(basis_state, 2)
        actual = statevector[index]
        expected = complex(expected_amplitude)
        error = abs(actual - expected)
        assert error <= tolerance
        return True
    
    def assert_amplitude_magnitude(self, circuit: QuantumCircuit, basis_state: str,
                                   expected_magnitude: float, tolerance: float = 1e-5) -> bool:
        statevector = self.get_statevector(circuit)
        index = int(basis_state, 2)
        actual_magnitude = abs(statevector[index])
        error = abs(actual_magnitude - expected_magnitude)
        assert error <= tolerance
        return True
