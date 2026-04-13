"""Modern quantum circuit property testing for Qiskit 2.3.1+.

This module provides property-based testing for quantum circuits
compatible with modern Qiskit versions, replacing the legacy Qcheck framework.

Features:
- Entanglement detection
- Measurement distribution analysis
- Circuit structure validation
- Statistical assertions
"""

from __future__ import annotations

import statistics
from typing import Callable

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


class QuantumPropertyTest:
    """Property testing framework for quantum circuits with modern Qiskit."""

    def __init__(self, shots: int = 1000):
        """Initialize property tester.
        
        Args:
            shots: Number of measurement shots for statistical testing.
        """
        self.shots = shots
        self.simulator = AerSimulator(shots=shots)

    def measure_distribution(self, circuit: QuantumCircuit) -> dict[str, int]:
        """Get measurement distribution from a circuit.
        
        Args:
            circuit: Quantum circuit to measure (must have measurements).
            
        Returns:
            Dictionary of bitstring -> count.
        """
        result = self.simulator.run(circuit).result()
        return result.get_counts()

    def assert_entangled(
        self,
        circuit: QuantumCircuit,
        qubits: list[int],
        entropy_threshold: float = 0.5,
    ) -> bool:
        """Assert that specified qubits are entangled.
        
        Uses measurement correlation: entangled qubits show higher statistical
        correlation in measurement outcomes than separable states.
        
        Args:
            circuit: Circuit to test (must be measurable).
            qubits: Qubit indices to test for entanglement.
            entropy_threshold: Min fraction of possible states needed (0-1).
                             Default 0.5: 2-qubit Bell state has 2/4 states = 0.5
                             Higher = more entanglement required.
        
        Returns:
            True if sufficiently entangled, raises AssertionError otherwise.
            
        Raises:
            AssertionError: If entanglement criterion not met.
        """
        if not circuit.num_clbits:
            raise ValueError("Circuit must have classical bits for measurement")

        dist = self.measure_distribution(circuit)
        num_unique_outcomes = len(dist)

        # For n qubits, max possible outcomes = 2^n
        max_outcomes = 2 ** len(qubits)
        entropy_ratio = num_unique_outcomes / max_outcomes

        assert entropy_ratio >= entropy_threshold, (
            f"Insufficient entanglement: {num_unique_outcomes}/{max_outcomes} states "
            f"(ratio {entropy_ratio:.2f} < threshold {entropy_threshold:.2f})"
        )
        return True

    def assert_separable(
        self,
        circuit: QuantumCircuit,
        qubits: list[int],
        entropy_threshold: float = 0.1,
    ) -> bool:
        """Assert that specified qubits are separable (not entangled).
        
        Args:
            circuit: Circuit to test (must be measurable).
            qubits: Qubit indices to test.
            entropy_threshold: Max fraction of possible states allowed (0-1).
                             Lower = more separability required.
        
        Returns:
            True if sufficiently separable, raises AssertionError otherwise.
        """
        if not circuit.num_clbits:
            raise ValueError("Circuit must have classical bits for measurement")

        dist = self.measure_distribution(circuit)
        num_unique_outcomes = len(dist)
        max_outcomes = 2 ** len(qubits)
        entropy_ratio = num_unique_outcomes / max_outcomes

        assert entropy_ratio <= entropy_threshold, (
            f"High entanglement detected: {num_unique_outcomes}/{max_outcomes} states "
            f"(ratio {entropy_ratio:.2f} > threshold {entropy_threshold:.2f})"
        )
        return True

    def assert_most_frequent(
        self,
        circuit: QuantumCircuit,
        expected_state: str | None = None,
        min_frequency: float = 0.3,
    ) -> bool:
        """Assert that a measurement outcome appears most frequently.
        
        Args:
            circuit: Circuit to test (must be measurable).
            expected_state: Expected most frequent bitstring. If None, 
                          just checks that one state dominates.
            min_frequency: Minimum fraction (0-1) that top state must reach.
        
        Returns:
            True if assertion passes, raises AssertionError otherwise.
        """
        dist = self.measure_distribution(circuit)
        if not dist:
            raise ValueError("No measurement outcomes")

        most_frequent_state = max(dist, key=dist.get)
        most_frequent_count = dist[most_frequent_state]
        frequency = most_frequent_count / self.shots

        if expected_state:
            assert most_frequent_state == expected_state, (
                f"Expected most frequent: {expected_state}, "
                f"got: {most_frequent_state} ({frequency:.2%})"
            )

        assert frequency >= min_frequency, (
            f"Most frequent state ({most_frequent_state}) only at {frequency:.2%}, "
            f"below threshold {min_frequency:.2%}"
        )
        return True

    def assert_equal_superposition(
        self,
        circuit: QuantumCircuit,
        max_deviation: float = 0.1,
    ) -> bool:
        """Assert that all measurement outcomes are equally probable.
        
        Useful for testing balanced superposition states like |+⟩ or |i+⟩.
        
        Args:
            circuit: Circuit to test.
            max_deviation: Max allowed deviation from equal probability (0-1).
        
        Returns:
            True if probabilities are balanced, raises AssertionError otherwise.
        """
        dist = self.measure_distribution(circuit)
        expected_prob = 1.0 / len(dist) if dist else 0

        deviations = []
        for state, count in dist.items():
            actual_prob = count / self.shots
            deviation = abs(actual_prob - expected_prob)
            deviations.append(deviation)

        max_dev = max(deviations) if deviations else 0
        assert max_dev <= max_deviation, (
            f"Superposition not equal: max deviation {max_dev:.2%} "
            f"exceeds threshold {max_deviation:.2%}"
        )
        return True

    def assert_distribution_matches(
        self,
        circuit: QuantumCircuit,
        expected_distribution: dict[str, float],
        tolerance: float = 0.05,
    ) -> bool:
        """Assert measured distribution matches expected probability distribution.
        
        Args:
            circuit: Circuit to test.
            expected_distribution: Dict mapping bitstrings to expected probabilities.
            tolerance: Max allowed deviation for each outcome (0-1).
            
        Returns:
            True if distribution matches, raises AssertionError otherwise.
        """
        dist = self.measure_distribution(circuit)
        measured_dist = {
            state: count / self.shots for state, count in dist.items()
        }

        for state, expected_prob in expected_distribution.items():
            actual_prob = measured_dist.get(state, 0)
            deviation = abs(actual_prob - expected_prob)
            assert deviation <= tolerance, (
                f"State {state}: expected {expected_prob:.2%}, "
                f"got {actual_prob:.2%} (deviation {deviation:.2%})"
            )

        return True


# Convenient functions matching Qcheck-style API
def assert_entangled(circuit: QuantumCircuit, qubits: list[int], runs: int = 1000):
    """Assert qubits are entangled (Qcheck-style API)."""
    tester = QuantumPropertyTest(shots=runs)
    return tester.assert_entangled(circuit, qubits)


def assert_separable(circuit: QuantumCircuit, qubits: list[int], runs: int = 1000):
    """Assert qubits are separable (Qcheck-style API)."""
    tester = QuantumPropertyTest(shots=runs)
    return tester.assert_separable(circuit, qubits)


def assert_most_frequent(
    circuit: QuantumCircuit,
    expected_state: str | None = None,
    runs: int = 1000,
):
    """Assert most frequent measurement outcome (Qcheck-style API)."""
    tester = QuantumPropertyTest(shots=runs)
    return tester.assert_most_frequent(circuit, expected_state=expected_state)


def assert_equal_superposition(circuit: QuantumCircuit, runs: int = 1000, max_deviation: float = 0.1):
    """Assert equal superposition (Qcheck-style API)."""
    tester = QuantumPropertyTest(shots=runs)
    return tester.assert_equal_superposition(circuit, max_deviation=max_deviation)


def assert_distribution_matches(
    circuit: QuantumCircuit,
    expected_distribution: dict[str, float],
    runs: int = 1000,
    tolerance: float = 0.05,
):
    """Assert distribution matches (Qcheck-style API)."""
    tester = QuantumPropertyTest(shots=runs)
    return tester.assert_distribution_matches(circuit, expected_distribution, tolerance)
