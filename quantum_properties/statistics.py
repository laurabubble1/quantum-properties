"""Statistical analysis and hypothesis testing for quantum circuits."""

from __future__ import annotations

import math
from typing import NamedTuple

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


class ChiSquareTest(NamedTuple):
    """Chi-square goodness-of-fit test result."""
    statistic: float
    p_value: float
    degrees_of_freedom: int
    significant: bool  # True if p-value < 0.05


class CorrelationAnalysis(NamedTuple):
    """Correlation analysis between qubits."""
    qubit_pair: tuple[int, int]
    correlation: float  # -1 to 1
    mutual_information: float  # 0 to entropy


class QuantumStatistics:
    """Statistical analysis tools for quantum circuits."""
    
    def __init__(self, shots: int = 1000):
        """Initialize statistics calculator.
        
        Args:
            shots: Number of measurement shots
        """
        self.shots = shots
        self.simulator = AerSimulator(shots=shots)
    
    def chi_square_test(
        self,
        circuit: QuantumCircuit,
        expected_distribution: dict[str, float] | None = None,
    ) -> ChiSquareTest:
        """Perform chi-square goodness-of-fit test.
        
        Tests if measured distribution matches expected (uniform if not specified).
        
        Args:
            circuit: Circuit to test
            expected_distribution: Expected probability distribution.
                                 None = uniform distribution.
        
        Returns:
            ChiSquareTest result
        """
        if not circuit.num_clbits:
            raise ValueError("Circuit must have classical bits for measurement")
        
        # Get measurement distribution
        result = self.simulator.run(circuit).result()
        counts = result.get_counts()
        
        # Setup expected distribution
        if expected_distribution is None:
            # Uniform distribution
            num_outcomes = 2 ** circuit.num_clbits
            expected_distribution = {
                format(i, f'0{circuit.num_clbits}b'): 1.0 / num_outcomes
                for i in range(num_outcomes)
            }
        
        # Calculate chi-square statistic
        chi_square = 0.0
        for state, expected_prob in expected_distribution.items():
            observed = counts.get(state, 0)
            expected = expected_prob * self.shots
            
            if expected > 0:
                chi_square += (observed - expected) ** 2 / expected
        
        # Degrees of freedom
        dof = len(expected_distribution) - 1
        
        # Approximate p-value (simple threshold)
        # Critical value for p=0.05, df=1 is 3.841
        p_value = 0.05 if chi_square < 3.841 else 0.01
        
        return ChiSquareTest(
            statistic=chi_square,
            p_value=p_value,
            degrees_of_freedom=dof,
            significant=chi_square > 3.841,
        )
    
    def qubit_correlation(
        self,
        circuit: QuantumCircuit,
        qubit1: int,
        qubit2: int,
    ) -> CorrelationAnalysis:
        """Calculate correlation between two qubits' measurement outcomes.
        
        Correlation = (P(00) + P(11) - P(01) - P(10))
        Range: -1 (anti-correlated) to 1 (correlated)
        
        Args:
            circuit: Circuit to analyze
            qubit1: First qubit index
            qubit2: Second qubit index
            
        Returns:
            CorrelationAnalysis with correlation coefficient
        """
        if not circuit.num_clbits:
            raise ValueError("Circuit must have classical bits for measurement")
        
        result = self.simulator.run(circuit).result()
        counts = result.get_counts()
        
        # Get probabilities for 2-qubit outcomes
        total = sum(counts.values())
        probs = {state: count / total for state, count in counts.items()}
        
        # Extract bit strings for the specific qubits
        p_both_0 = 0.0  # P(qubit1=0, qubit2=0)
        p_both_1 = 0.0
        p_01 = 0.0
        p_10 = 0.0
        
        for bitstring, prob in probs.items():
            bit1 = int(bitstring[qubit1]) if qubit1 < len(bitstring) else 0
            bit2 = int(bitstring[qubit2]) if qubit2 < len(bitstring) else 0
            
            if bit1 == 0 and bit2 == 0:
                p_both_0 += prob
            elif bit1 == 1 and bit2 == 1:
                p_both_1 += prob
            elif bit1 == 0 and bit2 == 1:
                p_01 += prob
            else:
                p_10 += prob
        
        # Calculate correlation
        correlation = p_both_0 + p_both_1 - p_01 - p_10
        
        # Mutual information approximation
        # I(X;Y) = H(X) + H(Y) - H(X,Y)
        def entropy(p: float) -> float:
            if 0 < p < 1:
                return -p * math.log2(p) - (1 - p) * math.log2(1 - p)
            return 0.0
        
        # Marginal entropies
        p_qubit1_0 = (p_both_0 + p_01)
        p_qubit2_0 = (p_both_0 + p_10)
        
        h_qubit1 = entropy(p_qubit1_0)
        h_qubit2 = entropy(p_qubit2_0)
        
        # Joint entropy
        h_joint = (
            -p_both_0 * math.log2(p_both_0 + 1e-10)
            - p_both_1 * math.log2(p_both_1 + 1e-10)
            - p_01 * math.log2(p_01 + 1e-10)
            - p_10 * math.log2(p_10 + 1e-10)
        )
        
        mutual_info = max(0, h_qubit1 + h_qubit2 - h_joint)
        
        return CorrelationAnalysis(
            qubit_pair=(qubit1, qubit2),
            correlation=correlation,
            mutual_information=mutual_info,
        )
    
    def entanglement_entropy(self, circuit: QuantumCircuit) -> float:
        """Estimate entanglement using measurement entropy.
        
        Higher entropy = more entanglement
        
        Args:
            circuit: Circuit to analyze
            
        Returns:
            Shannon entropy of measurement distribution (0 to max_entropy)
        """
        result = self.simulator.run(circuit).result()
        counts = result.get_counts()
        
        # Calculate Shannon entropy
        entropy = 0.0
        for count in counts.values():
            prob = count / self.shots
            if prob > 0:
                entropy -= prob * math.log2(prob)
        
        return entropy
    
    def distribution_fidelity(
        self,
        circuit: QuantumCircuit,
        reference_distribution: dict[str, float],
    ) -> float:
        """Calculate fidelity between measured and reference distributions.
        
        Fidelity ranges from 0 (completely different) to 1 (identical).
        
        Args:
            circuit: Circuit to measure
            reference_distribution: Target probability distribution
            
        Returns:
            Fidelity value (0.0 to 1.0)
        """
        result = self.simulator.run(circuit).result()
        counts = result.get_counts()
        measured = {state: count / self.shots for state, count in counts.items()}
        
        # Bhattacharyya coefficient (approximates fidelity)
        fidelity = 0.0
        for state in reference_distribution:
            m_prob = measured.get(state, 0.0)
            r_prob = reference_distribution.get(state, 0.0)
            fidelity += math.sqrt(m_prob * r_prob)
        
        return fidelity
