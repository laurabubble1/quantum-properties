"""Noise simulation for quantum circuits.

Test circuits with realistic quantum noise models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, amplitude_damping_error


class NoiseConfig(NamedTuple):
    """Noise model configuration."""
    single_qubit_error_rate: float
    two_qubit_error_rate: float
    amplitude_damping_rate: float


@dataclass
class NoiseImpactAnalysis:
    """Analysis of noise impact on circuit."""
    circuit_name: str
    clean_distribution: dict[str, int]
    noisy_distribution: dict[str, int]
    fidelity_loss: float  # 0 to 1, higher = more noise impact
    error_rate_increase: float  # Percentage increase in errors


class NoiseSimulator:
    """Simulate quantum circuits with noise."""
    
    # Common noise profiles
    DEFAULT_NOISE = NoiseConfig(
        single_qubit_error_rate=0.001,
        two_qubit_error_rate=0.01,
        amplitude_damping_rate=0.001,
    )
    
    LOW_NOISE = NoiseConfig(
        single_qubit_error_rate=0.0001,
        two_qubit_error_rate=0.001,
        amplitude_damping_rate=0.0001,
    )
    
    HIGH_NOISE = NoiseConfig(
        single_qubit_error_rate=0.01,
        two_qubit_error_rate=0.05,
        amplitude_damping_rate=0.01,
    )
    
    HARDWARE_LIKE = NoiseConfig(
        single_qubit_error_rate=0.002,
        two_qubit_error_rate=0.020,
        amplitude_damping_rate=0.001,
    )
    
    def __init__(self, noise_config: NoiseConfig | None = None, shots: int = 1000):
        """Initialize noise simulator.
        
        Args:
            noise_config: Noise configuration. Defaults to DEFAULT_NOISE.
            shots: Number of measurement shots
        """
        self.noise_config = noise_config or self.DEFAULT_NOISE
        self.shots = shots
    
    def _build_noise_model(self) -> NoiseModel:
        """Build Qiskit NoiseModel from configuration.
        
        Returns:
            Configured NoiseModel
        """
        noise_model = NoiseModel()
        
        # Single-qubit depolarizing errors
        single_error = depolarizing_error(
            self.noise_config.single_qubit_error_rate, 1
        )
        noise_model.add_all_qubit_quantum_errors(single_error, ['h', 'x', 'y', 'z', 's', 't'])
        
        # Two-qubit depolarizing errors
        two_qubit_error = depolarizing_error(self.noise_config.two_qubit_error_rate, 2)
        noise_model.add_all_qubit_quantum_errors(two_qubit_error, ['cx', 'cz'])
        
        # Amplitude damping
        amp_damp = amplitude_damping_error(self.noise_config.amplitude_damping_rate)
        noise_model.add_all_qubit_quantum_errors(amp_damp, ['h', 'x', 'y', 'z'])
        
        return noise_model
    
    def run_circuit(self, circuit: QuantumCircuit) -> dict[str, int]:
        """Run circuit with noise.
        
        Args:
            circuit: Circuit to run
            
        Returns:
            Measurement results as count dictionary
        """
        noise_model = self._build_noise_model()
        simulator = AerSimulator(noise_model=noise_model, shots=self.shots)
        
        result = simulator.run(circuit).result()
        return result.get_counts(circuit)
    
    def run_circuit_clean(self, circuit: QuantumCircuit) -> dict[str, int]:
        """Run circuit without noise (ideal).
        
        Args:
            circuit: Circuit to run
            
        Returns:
            Ideal measurement results
        """
        simulator = AerSimulator(shots=self.shots)
        result = simulator.run(circuit).result()
        return result.get_counts(circuit)
    
    def compare_with_ideal(self, circuit: QuantumCircuit) -> NoiseImpactAnalysis:
        """Compare noisy circuit results with ideal circuit.
        
        Args:
            circuit: Circuit to analyze
            
        Returns:
            NoiseImpactAnalysis with fidelity loss and error increase
        """
        clean_dist = self.run_circuit_clean(circuit)
        noisy_dist = self.run_circuit(circuit)
        
        # Calculate fidelity loss using total variation distance
        all_states = set(clean_dist.keys()) | set(noisy_dist.keys())
        
        fidelity_loss = 0.0
        for state in all_states:
            clean_prob = clean_dist.get(state, 0) / self.shots
            noisy_prob = noisy_dist.get(state, 0) / self.shots
            fidelity_loss += abs(clean_prob - noisy_prob) / 2.0
        
        # Calculate error increase
        # Errors = probability of getting wrong state
        clean_error_prob = 0.0
        noisy_error_prob = 0.0
        
        for state in all_states:
            if clean_dist.get(state, 0) > 0:
                clean_error_prob += clean_dist[state] / self.shots
            
            # Consider it error if not in ideal distribution
            if state not in clean_dist:
                noisy_error_prob += noisy_dist.get(state, 0) / self.shots
        
        # More practical error metric: states we don't want
        unwanted_in_clean = sum(
            count for state, count in clean_dist.items()
            if count < self.shots / 10
        ) / self.shots
        
        unwanted_in_noisy = sum(
            count for state, count in noisy_dist.items()
            if state not in clean_dist or clean_dist[state] < self.shots / 10
        ) / self.shots
        
        error_increase = max(0, unwanted_in_noisy - unwanted_in_clean)
        
        return NoiseImpactAnalysis(
            circuit_name=circuit.name or "Circuit",
            clean_distribution=clean_dist,
            noisy_distribution=noisy_dist,
            fidelity_loss=fidelity_loss,
            error_rate_increase=error_increase,
        )
    
    def assert_noise_robust(
        self,
        circuit: QuantumCircuit,
        max_fidelity_loss: float = 0.1,
    ) -> bool:
        """Assert circuit is robust to noise.
        
        Args:
            circuit: Circuit to test
            max_fidelity_loss: Maximum acceptable fidelity loss (0-1)
            
        Returns:
            True if fidelity loss is acceptable
        """
        analysis = self.compare_with_ideal(circuit)
        
        assert analysis.fidelity_loss <= max_fidelity_loss, (
            f"Circuit not noise robust: fidelity loss {analysis.fidelity_loss:.2%} "
            f"exceeds threshold {max_fidelity_loss:.2%}"
        )
        
        return True
    
    def assert_error_contained(
        self,
        circuit: QuantumCircuit,
        max_error_increase: float = 0.05,
    ) -> bool:
        """Assert noise doesn't cause excessive additional errors.
        
        Args:
            circuit: Circuit to test
            max_error_increase: Maximum acceptable error increase (0-1)
            
        Returns:
            True if error increase is acceptable
        """
        analysis = self.compare_with_ideal(circuit)
        
        assert analysis.error_rate_increase <= max_error_increase, (
            f"Circuit error increase too high: {analysis.error_rate_increase:.2%} "
            f"exceeds threshold {max_error_increase:.2%}"
        )
        
        return True
    
    def test_under_noise(
        self,
        circuit: QuantumCircuit,
        assertion_func: callable,
    ) -> bool:
        """Test if circuit passes assertion even with noise.
        
        Args:
            circuit: Circuit to test
            assertion_func: Function that tests circuit (should raise AssertionError on failure)
            
        Returns:
            True if circuit passes test with noise
        """
        # Run with noise
        try:
            # We need to measure the circuit to test it
            circuit_measured = circuit.copy()
            if circuit_measured.num_clbits == 0:
                circuit_measured.measure_all()
            
            # Run and get distribution
            counts = self.run_circuit(circuit_measured)
            
            # Call assertion - this might fail
            result = assertion_func(counts)
            return result is True or result is not None
        except AssertionError:
            return False
