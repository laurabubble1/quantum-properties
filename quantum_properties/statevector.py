"""State vector verification for quantum circuits.

Test circuits by examining exact quantum state amplitudes.
"""

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
    fidelity: float  # 0 to 1


class StateVectorVerifier:
    """Verify quantum circuits using exact state vectors."""
    
    def __init__(self):
        """Initialize state vector verifier."""
        self.simulator = AerSimulator(method='statevector')
    
    def get_statevector(self, circuit: QuantumCircuit) -> list[complex]:
        """Get exact statevector for circuit.
        
        Args:
            circuit: Circuit to simulate
            
        Returns:
            Statevector as list of complex amplitudes
        """
        # Create a copy without measurements for statevector
        qc_copy = circuit.copy()
        
        # Remove measurements if present
        if hasattr(qc_copy, 'data'):
            qc_copy.data = [instr for instr in qc_copy.data 
                           if instr[0].name not in ['measure', 'reset']]
        
        result = self.simulator.run(qc_copy).result()
        return result.get_statevector(qc_copy).data.tolist()
    
    def assert_amplitude(
        self,
        circuit: QuantumCircuit,
        basis_state: str,
        expected_amplitude: complex | float,
        tolerance: float = 1e-5,
    ) -> bool:
        """Assert amplitude of a specific basis state.
        
        Args:
            circuit: Circuit to test
            basis_state: Basis state (e.g., "101")
            expected_amplitude: Expected amplitude (can be magnitude if real)
            tolerance: Maximum allowed deviation
            
        Returns:
            True if amplitude matches, raises AssertionError otherwise
        """
        statevector = self.get_statevector(circuit)
        index = int(basis_state, 2)
        
        if index >= len(statevector):
            raise ValueError(f"Basis state {basis_state} out of range")
        
        actual = statevector[index]
        expected = complex(expected_amplitude) if not isinstance(expected_amplitude, complex) else expected_amplitude
        
        error = abs(actual - expected)
        
        assert error <= tolerance, (
            f"Amplitude mismatch for |{basis_state}⟩: "
            f"expected {expected:.4f}, got {actual:.4f} (error {error:.4e})"
        )
        
        return True
    
    def assert_amplitude_magnitude(
        self,
        circuit: QuantumCircuit,
        basis_state: str,
        expected_magnitude: float,
        tolerance: float = 1e-5,
    ) -> bool:
        """Assert magnitude of amplitude (probability amplitude).
        
        Args:
            circuit: Circuit to test
            basis_state: Basis state (e.g., "101")
            expected_magnitude: Expected magnitude |α|
            tolerance: Maximum allowed deviation
            
        Returns:
            True if magnitude matches
        """
        statevector = self.get_statevector(circuit)
        index = int(basis_state, 2)
        
        if index >= len(statevector):
            raise ValueError(f"Basis state {basis_state} out of range")
        
        actual_magnitude = abs(statevector[index])
        error = abs(actual_magnitude - expected_magnitude)
        
        assert error <= tolerance, (
            f"Amplitude magnitude mismatch for |{basis_state}⟩: "
            f"expected {expected_magnitude:.4f}, got {actual_magnitude:.4f}"
        )
        
        return True
    
    def assert_amplitudes(
        self,
        circuit: QuantumCircuit,
        expected_amplitudes: dict[str, complex | float],
        tolerance: float = 1e-5,
    ) -> bool:
        """Assert multiple amplitudes at once.
        
        Args:
            circuit: Circuit to test
            expected_amplitudes: Dict mapping basis states to amplitudes
            tolerance: Maximum allowed deviation
            
        Returns:
            True if all amplitudes match
        """
        statevector = self.get_statevector(circuit)
        
        for basis_state, expected_amp in expected_amplitudes.items():
            index = int(basis_state, 2)
            actual = statevector[index]
            expected = complex(expected_amp)
            
            error = abs(actual - expected)
            assert error <= tolerance, (
                f"Amplitude mismatch for |{basis_state}⟩: "
                f"expected {expected:.4f}, got {actual:.4f}"
            )
        
        return True
    
    def assert_product_state(
        self,
        circuit: QuantumCircuit,
        expected_state: str,
        tolerance: float = 1e-5,
    ) -> bool:
        """Assert circuit produces a specific product (separable) state.
        
        Args:
            circuit: Circuit to test
            expected_state: Expected basis state (e.g., "010")
            tolerance: Maximum allowed deviation from |expected⟩
            
        Returns:
            True if state matches
        """
        statevector = self.get_statevector(circuit)
        
        # Expected state should have amplitude 1 at one position
        expected_index = int(expected_state, 2)
        
        for i, amplitude in enumerate(statevector):
            if i == expected_index:
                assert abs(abs(amplitude) - 1.0) < tolerance, (
                    f"Expected amplitude 1.0 at |{expected_state}⟩, got {abs(amplitude):.4f}"
                )
            else:
                assert abs(amplitude) < tolerance, (
                    f"Expected amplitude 0.0 at |{format(i, f'0{len(expected_state)}b')}⟩, got {abs(amplitude):.4f}"
                )
        
        return True
    
    def assert_equal_superposition(
        self,
        circuit: QuantumCircuit,
        num_qubits: int,
        tolerance: float = 1e-5,
    ) -> bool:
        """Assert circuit produces equal superposition of all basis states.
        
        Args:
            circuit: Circuit to test
            num_qubits: Number of qubits
            tolerance: Maximum allowed deviation from 1/√(2^n)
            
        Returns:
            True if superposition is balanced
        """
        statevector = self.get_statevector(circuit)
        num_states = 2 ** num_qubits
        expected_magnitude = 1.0 / math.sqrt(num_states)
        
        for i, amplitude in enumerate(statevector[:num_states]):
            actual_magnitude = abs(amplitude)
            error = abs(actual_magnitude - expected_magnitude)
            
            assert error < tolerance, (
                f"Unbalanced superposition at |{format(i, f'0{num_qubits}b')}⟩: "
                f"expected magnitude {expected_magnitude:.4f}, got {actual_magnitude:.4f}"
            )
        
        return True
    
    def compare_amplitudes(
        self,
        circuit: QuantumCircuit,
        reference_amplitudes: dict[str, complex | float],
    ) -> list[AmplitudeComparison]:
        """Compare circuit amplitudes with reference values.
        
        Args:
            circuit: Circuit to test
            reference_amplitudes: Reference amplitude values
            
        Returns:
            List of AmplitudeComparison objects
        """
        statevector = self.get_statevector(circuit)
        comparisons = []
        
        for basis_state, ref_amp in reference_amplitudes.items():
            index = int(basis_state, 2)
            circuit_amp = statevector[index] if index < len(statevector) else 0
            ref_complex = complex(ref_amp)
            
            # Fidelity between two complex numbers
            fidelity = abs(circuit_amp * ref_complex.conjugate())
            
            comparisons.append(AmplitudeComparison(
                basis_state=basis_state,
                circuit_amplitude=circuit_amp,
                reference_amplitude=ref_complex,
                fidelity=fidelity,
            ))
        
        return comparisons
    
    def global_phase_invariant_compare(
        self,
        circuit: QuantumCircuit,
        reference_state: dict[str, complex | float],
        tolerance: float = 1e-5,
    ) -> bool:
        """Compare states ignoring global phase.
        
        Two states differing only by e^(iθ) are physically equivalent.
        
        Args:
            circuit: Circuit to test
            reference_state: Reference amplitudes
            tolerance: Maximum allowed deviation
            
        Returns:
            True if states match up to global phase
        """
        statevector = self.get_statevector(circuit)
        
        # Find first non-zero amplitude to get phase reference
        phase_ref = None
        for i, amplitude in enumerate(statevector):
            if abs(amplitude) > tolerance:
                phase_ref = cmath.phase(amplitude)
                break
        
        if phase_ref is None:
            raise ValueError("All amplitudes are zero")
        
        # Check all amplitudes accounting for phase
        for basis_state, expected_amp in reference_state.items():
            index = int(basis_state, 2)
            actual = statevector[index]
            expected = complex(expected_amp)
            
            # Remove global phase
            if abs(expected) > tolerance:
                phase_exp = cmath.phase(expected)
                phase_diff = phase_ref - phase_exp
                
                # Rotate expected by phase difference
                expected_rotated = expected * cmath.exp(1j * phase_diff)
                error = abs(actual - expected_rotated)
            else:
                error = abs(actual)
            
            assert error <= tolerance, (
                f"Amplitude mismatch for |{basis_state}⟩ (phase-invariant): "
                f"expected {expected:.4f}, got {actual:.4f}"
            )
        
        return True
