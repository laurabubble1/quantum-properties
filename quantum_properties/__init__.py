"""Quantum Property Testing Framework for Qiskit 2.3.1+

A modern replacement for Qcheck, providing comprehensive property-based testing assertions
for quantum circuits compatible with current Qiskit versions.

Features:
- Property definition framework (decorators, builders)
- Statistical analysis (chi-square, correlation, fidelity)
- State vector verification (amplitudes, superposition)
- Noise simulation (error models, robustness testing)
- Advanced reporting (text, HTML, visualizations)

Example:
    >>> from qiskit import QuantumCircuit
    >>> from quantum_properties import PropertyBuilder
    >>> 
    >>> builder = PropertyBuilder(shots=1000)
    >>> 
    >>> @builder.define("Bell state is entangled")
    >>> def test_entanglement(circuit):
    ...     return builder.assert_entangled(circuit, [0, 1])
    >>> 
    >>> circuit = QuantumCircuit(2, 2)
    >>> circuit.h(0)
    >>> circuit.cx(0, 1)
    >>> circuit.measure([0, 1], [0, 1])
    >>> 
    >>> results = builder.test_circuit(circuit)
    >>> print(builder.report(results))
"""

# Core assertions
from quantum_properties.core import (
    QuantumPropertyTest,
    assert_entangled,
    assert_separable,
    assert_most_frequent,
    assert_equal_superposition,
    assert_distribution_matches,
)

# Property definition framework
from quantum_properties.properties import (
    PropertyBuilder,
    QuantumProperty,
    PropertyResult,
)

# Statistical analysis
from quantum_properties.statistics import (
    QuantumStatistics,
    ChiSquareTest,
    CorrelationAnalysis,
)

# State vector verification
from quantum_properties.statevector import (
    StateVectorVerifier,
    AmplitudeComparison,
)

# Noise simulation
from quantum_properties.noise import (
    NoiseSimulator,
    NoiseConfig,
    NoiseImpactAnalysis,
)

# Reporting
from quantum_properties.reporting import (
    CircuitReport,
    CircuitMetrics,
    ReportFormatter,
    HTMLReport,
)

__version__ = "0.2.0"
__author__ = "Laura Bubble"

__all__ = [
    # Core
    "QuantumPropertyTest",
    "assert_entangled",
    "assert_separable",
    "assert_most_frequent",
    "assert_equal_superposition",
    "assert_distribution_matches",
    
    # Properties
    "PropertyBuilder",
    "QuantumProperty",
    "PropertyResult",
    
    # Statistics
    "QuantumStatistics",
    "ChiSquareTest",
    "CorrelationAnalysis",
    
    # State Vector
    "StateVectorVerifier",
    "AmplitudeComparison",
    
    # Noise
    "NoiseSimulator",
    "NoiseConfig",
    "NoiseImpactAnalysis",
    
    # Reporting
    "CircuitReport",
    "CircuitMetrics",
    "ReportFormatter",
    "HTMLReport",
]
