"""Property definition framework for quantum circuits.

Allows defining reusable properties that can be tested across multiple circuits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any
from functools import wraps

from qiskit import QuantumCircuit

from quantum_properties.core import QuantumPropertyTest


@dataclass
class PropertyResult:
    """Result of a property test."""
    name: str
    passed: bool
    error: str | None = None
    stats: dict[str, Any] | None = None
    
    def __str__(self) -> str:
        status = "✓ PASS" if self.passed else "✗ FAIL"
        msg = f"{status}: {self.name}"
        if self.error:
            msg += f" - {self.error}"
        return msg


class QuantumProperty:
    """Decorator-based property definition for quantum circuits."""
    
    def __init__(self, name: str | None = None, runs: int = 1000):
        """Initialize property.
        
        Args:
            name: Property name (defaults to function name)
            runs: Number of measurement shots
        """
        self.name = name
        self.runs = runs
        self.tests: list[Callable] = []
    
    def __call__(self, func: Callable) -> Callable | Any:
        """Register function as property definition or execute property."""
        if callable(func) and not isinstance(func, QuantumCircuit):
            # Being used as @property decorator
            self.name = self.name or func.__name__
            
            @wraps(func)
            def wrapper(circuit: QuantumCircuit) -> PropertyResult:
                try:
                    result = func(circuit, self.runs)
                    return PropertyResult(
                        name=self.name,
                        passed=result is True or (isinstance(result, dict) and result.get('passed', False)),
                        stats=result if isinstance(result, dict) else None
                    )
                except AssertionError as e:
                    return PropertyResult(name=self.name, passed=False, error=str(e))
                except Exception as e:
                    return PropertyResult(name=self.name, passed=False, error=f"Error: {str(e)}")
            
            return wrapper
        return func


class PropertyBuilder:
    """Build and test quantum circuit properties."""
    
    def __init__(self, shots: int = 1000):
        """Initialize property builder.
        
        Args:
            shots: Number of measurement shots for tests
        """
        self.shots = shots
        self.properties: dict[str, Callable] = {}
        self.tester = QuantumPropertyTest(shots=shots)
    
    def define(self, name: str) -> Callable:
        """Define a new property.
        
        Args:
            name: Property name
            
        Returns:
            Decorator function
            
        Example:
            >>> builder = PropertyBuilder()
            >>> 
            >>> @builder.define("Bell state is entangled")
            >>> def check_bell_entanglement(circuit):
            ...     return builder.assert_entangled(circuit, [0, 1])
        """
        def decorator(func: Callable) -> Callable:
            self.properties[name] = func
            
            @wraps(func)
            def wrapper(circuit: QuantumCircuit) -> PropertyResult:
                try:
                    result = func(circuit)
                    if isinstance(result, bool):
                        return PropertyResult(name=name, passed=result)
                    else:
                        return PropertyResult(name=name, passed=True, stats=result)
                except AssertionError as e:
                    return PropertyResult(name=name, passed=False, error=str(e))
                except Exception as e:
                    return PropertyResult(name=name, passed=False, error=str(e))
            
            return wrapper
        
        return decorator
    
    def assert_entangled(self, circuit: QuantumCircuit, qubits: list[int]) -> bool:
        """Assert qubits are entangled."""
        return self.tester.assert_entangled(circuit, qubits)
    
    def assert_separable(self, circuit: QuantumCircuit, qubits: list[int]) -> bool:
        """Assert qubits are separable."""
        return self.tester.assert_separable(circuit, qubits)
    
    def assert_most_frequent(
        self,
        circuit: QuantumCircuit,
        expected_state: str | None = None,
        min_frequency: float = 0.3,
    ) -> bool:
        """Assert most frequent measurement outcome."""
        return self.tester.assert_most_frequent(circuit, expected_state, min_frequency)
    
    def assert_equal_superposition(
        self,
        circuit: QuantumCircuit,
        max_deviation: float = 0.1,
    ) -> bool:
        """Assert equal superposition."""
        return self.tester.assert_equal_superposition(circuit, max_deviation)
    
    def assert_distribution_matches(
        self,
        circuit: QuantumCircuit,
        expected_distribution: dict[str, float],
        tolerance: float = 0.05,
    ) -> bool:
        """Assert distribution matches expected."""
        return self.tester.assert_distribution_matches(
            circuit, expected_distribution, tolerance
        )
    
    def test_circuit(self, circuit: QuantumCircuit) -> list[PropertyResult]:
        """Test circuit against all defined properties.
        
        Args:
            circuit: Circuit to test
            
        Returns:
            List of PropertyResult objects
        """
        results = []
        for name, prop_func in self.properties.items():
            try:
                result_val = prop_func(circuit)
                if isinstance(result_val, PropertyResult):
                    results.append(result_val)
                else:
                    passed = result_val is True or (isinstance(result_val, dict) and result_val.get('passed', False))
                    results.append(PropertyResult(name=name, passed=passed))
            except Exception as e:
                results.append(PropertyResult(name=name, passed=False, error=str(e)))
        
        return results
    
    def test_batch(self, circuits: dict[str, QuantumCircuit]) -> dict[str, list[PropertyResult]]:
        """Test multiple circuits against all properties.
        
        Args:
            circuits: Dict mapping circuit name to circuit
            
        Returns:
            Dict mapping circuit name to their test results
        """
        return {name: self.test_circuit(circuit) for name, circuit in circuits.items()}
    
    def report(self, results: list[PropertyResult]) -> str:
        """Generate test report.
        
        Args:
            results: List of PropertyResult objects
            
        Returns:
            Formatted report string
        """
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        
        lines = [
            f"Property Test Report: {passed}/{total} passed",
            "=" * 50,
        ]
        
        for result in results:
            lines.append(str(result))
        
        lines.append("=" * 50)
        
        return "\n".join(lines)
