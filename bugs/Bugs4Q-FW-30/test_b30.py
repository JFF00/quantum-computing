from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit, Aer, execute
import unittest
from qiskit.test import *


class TestAerSimulation(QiskitTestCase,unittest.TestCase):
    def test_f30(self):
        # Initialize circuit
        m_qubit = QuantumRegister(1)
        search_register = QuantumRegister(4)
        result_register = ClassicalRegister(4)
        ancillaries = QuantumRegister(3)
        circuit = QuantumCircuit(search_register, result_register, m_qubit, ancillaries)

        # Put M qubit into 1-superposition
        circuit.x(m_qubit)
        circuit.h(m_qubit)

        # Put search qubits into superposition
        circuit.h(search_register)

        for _ in range(2):

            # Encode S1 * !S2 * S3
            circuit.x( search_register[2] )
            circuit.ccx( search_register[1], search_register[2], ancillaries[0] )
            circuit.ccx( search_register[3], ancillaries[0], ancillaries[1] )
            circuit.x( search_register[2] )

            # Encode S0 * S1
            circuit.ccx( search_register[0], search_register[1], ancillaries[2] )

            # Encode oracle ((S0 * S1) + (S1 * !S2 * S3))
            circuit.x(ancillaries)
            circuit.ccx( ancillaries[1], ancillaries[2], m_qubit[0] )
            circuit.x(ancillaries)
            circuit.x(m_qubit)

            # Reset ancillaries to be used later
            circuit.reset(ancillaries)

            # Do rotation about the average
            circuit.h(search_register)
            circuit.x(search_register)
            circuit.ccx( search_register[0], search_register[1], ancillaries[0] )
            circuit.ccx( search_register[2], ancillaries[0], ancillaries[1] )
            circuit.ccx( search_register[3], ancillaries[1], m_qubit[0] )
            circuit.x(search_register)
            circuit.x(m_qubit)
            circuit.h(search_register)

            # Reset ancillaries for use later
            circuit.reset(ancillaries)
        
        circuit.measure(search_register, result_register)

        # Run the circuit with a given number of shots
        backend_sim = Aer.get_backend('qasm_simulator')
        shots = 2**17
        job_sim = execute(circuit, backend_sim, shots = shots)
        result_sim = job_sim.result()

        # get_counts returns a dictionary with the bit-strings as keys
        # and the number of times the string resulted as the value
        print(result_sim.get_counts(circuit))
        # Distribucion de la version fixed estimada con 10^6 shots (Aer 0.4.0);
        # se comparan frecuencias relativas con tolerancia absoluta 0.01
        expected = {'0000': 0.076, '0001': 0.057, '0010': 0.057, '0011': 0.076, '0100': 0.076, '0101': 0.057, '0110': 0.057, '0111': 0.077, '1000': 0.050, '1001': 0.050, '1010': 0.050, '1011': 0.050, '1100': 0.077, '1101': 0.057, '1110': 0.057, '1111': 0.076}
        freqs = {k: v / shots for k, v in result_sim.get_counts().items()}
        self.assertDictAlmostEqual(expected, freqs, delta=0.01)


if __name__ == '__main__':
    unittest.main(argv=[''])
