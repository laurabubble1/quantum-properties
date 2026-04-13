"""Quantum Property Testing Framework for Qiskit 2.3.1+

A modern replacement for Qcheck, providing property-based testing assertions
for quantum circuits compatible with current Qiskit versions.

Example:
    >>> from qiskit import QuantumCircuit
    >>> from quantum_properties import assert_entangled
    >>> 
    >>> circuit = QuantumCircuit(2, 2)
    >>> circuit.h(0)
    >>> circuit.cx(0, 1)
    >>> circuit.measure([0, 1], [0, 1])
    >>> 
    >>> assert_entangled(circuit, [0, 1])  # Passes!
"""

from quantum_properties.core import (
    QuantumPropertyTest,
    assert_entangled,
    assert_separable,
    assert_most_frequent,
    assert_equal_superposition,
    assert_distribution_matches,
)

__version__ = "0.1.0"
__author__ = "Laura Bubble"
__license__ = "Apache 2.0"

__all__ = [
    "QuantumPropertyTest",
    "assert_entangled",
    "assert_separable",
    "assert_most_frequent",
    "assert_equal_superposition",
    "assert_distribution_matches",
]
