# Quantum Properties

A modern property-based testing framework for [Qiskit](https://qiskit.org/) quantum circuits.

**Replaces the legacy Qcheck framework** with a clean, modern API compatible with Qiskit 2.3.1+.

## Capabilities

- ✅ **Entanglement Detection** - Assert qubits are entangled or separable
- ✅ **Distribution Analysis** - Verify measurement probability distributions  
- ✅ **Superposition Testing** - Assert balanced superposition states
- ✅ **State Frequency Testing** - Verify measurement outcome frequencies
- ✅ **Qiskit 2.3.1+ Compatible** - Works with current Qiskit versions
- ✅ **Simple API** - Both functional and class-based interfaces

## Installation

### From local directory

```bash
pip install -e /path/to/quantum-properties
```

### From GitHub (when published)

```bash
pip install quantum-properties
```

## Quick Start

```python
from qiskit import QuantumCircuit
from quantum_properties import assert_entangled

# Create a Bell state
circuit = QuantumCircuit(2, 2)
circuit.h(0)
circuit.cx(0, 1)
circuit.measure([0, 1], [0, 1])

# Assert the qubits are entangled
assert_entangled(circuit, [0, 1])  # ✓ Passes!
```

## Usage Examples

### Entanglement Testing

```python
from quantum_properties import assert_entangled, assert_separable

# Test for entanglement
assert_entangled(circuit, [0, 1], runs=1000)

# Test for separability
assert_separable(circuit, [0, 1], runs=1000)
```

### Distribution Matching

```python
from quantum_properties import assert_distribution_matches

# Create an equal superposition: (|0⟩ + |1⟩) / √2
circuit = QuantumCircuit(1, 1)
circuit.h(0)
circuit.measure(0, 0)

# Assert 50/50 distribution
expected = {"0": 0.5, "1": 0.5}
assert_distribution_matches(circuit, expected, tolerance=0.05)
```

### Superposition Testing

```python
from quantum_properties import assert_equal_superposition

# Create balanced superposition
circuit = QuantumCircuit(2, 2)
circuit.h(0)
circuit.h(1)
circuit.measure([0, 1], [0, 1])

# Verify all outcomes equally likely
assert_equal_superposition(circuit, max_deviation=0.1)
```

### Measurement Frequency Testing

```python
from quantum_properties import assert_most_frequent

# Create |0⟩ state (always measures to "0")
circuit = QuantumCircuit(1, 1)
circuit.measure(0, 0)

# Assert "0" is most frequent
assert_most_frequent(circuit, expected_state="0", runs=100)
```

## API Reference

### Functional Interface (Qcheck-style)

Perfect if you just need quick assertions:

```python
from quantum_properties import (
    assert_entangled,
    assert_separable,
    assert_most_frequent,
    assert_equal_superposition,
    assert_distribution_matches,
)

# All functions accept:
# - circuit: QuantumCircuit to test
# - Additional parameters specific to each assertion
# - runs: Number of measurement shots (default 1000)
```

### Class Interface

Use `QuantumPropertyTest` for fine-grained control:

```python
from quantum_properties import QuantumPropertyTest

tester = QuantumPropertyTest(shots=2000)

# Use methods with custom parameters
tester.assert_entangled(circuit, [0, 1], entropy_threshold=0.7)
tester.assert_equal_superposition(circuit, max_deviation=0.15)

# Get raw measurement distributions
dist = tester.measure_distribution(circuit)
print(dist)  # {"00": 245, "01": 262, "10": 251, "11": 242}
```

### Detailed Function Signatures

```python
def assert_entangled(
    circuit: QuantumCircuit,
    qubits: list[int],
    runs: int = 1000
) -> bool:
    """Assert qubits show entanglement patterns in measurement."""

def assert_separable(
    circuit: QuantumCircuit,
    qubits: list[int],
    runs: int = 1000
) -> bool:
    """Assert qubits do not show entanglement patterns."""

def assert_most_frequent(
    circuit: QuantumCircuit,
    expected_state: str | None = None,
    runs: int = 1000
) -> bool:
    """Assert one measurement outcome dominates."""

def assert_equal_superposition(
    circuit: QuantumCircuit,
    runs: int = 1000,
    max_deviation: float = 0.1
) -> bool:
    """Assert all outcomes equally probable."""

def assert_distribution_matches(
    circuit: QuantumCircuit,
    expected_distribution: dict[str, float],
    runs: int = 1000,
    tolerance: float = 0.05
) -> bool:
    """Assert measured distribution matches expected probabilities."""
```

## Requirements

- Python 3.10+
- Qiskit 2.0.0+
- Qiskit-Aer 0.17.0+
- NumPy 1.24.0+

## Development

### Setup development environment

```bash
git clone https://github.com/laurabubble1/quantum-properties.git
cd quantum-properties
pip install -e ".[dev]"
```

### Run tests

```bash
pytest tests/ -v
```

### Format code

```bash
black quantum_properties/ tests/
ruff check quantum_properties/ tests/
```

## Citation

If you use quantum-properties in your research, please cite:

```bibtex
@software{quantum_properties_2026,
  title={Quantum Properties: Property-Based Testing for Qiskit},
  author={Kubler, Laura},
  year={2026},
  url={https://github.com/laurabubble1/quantum-properties}
}
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

- 📖 [Documentation](./README.md)
- 🐛 [Issue Tracker](https://github.com/laurabubble1/quantum-properties/issues)
- 💬 [Discussions](https://github.com/laurabubble1/quantum-properties/discussions)
