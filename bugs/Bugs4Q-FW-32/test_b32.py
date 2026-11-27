import unittest
from qiskit import QuantumCircuit
from qiskit.circuit.quantumregister import QuantumRegister
from qiskit.circuit.classicalregister import ClassicalRegister
from qiskit import Aer, execute


def apply_measurement(circ):
    c = ClassicalRegister(len(circ.qubits), 'c')
    meas = QuantumCircuit(circ.qregs[0], c)
    meas.barrier(circ.qubits)
    meas.measure(circ.qubits, c)
    qc = circ + meas
    return qc


class Test(unittest.TestCase):
    def test_b32(self):
        qr = QuantumRegister(4)
        circ = QuantumCircuit(qr)
        for i in range(4):
            for j in range(i + 1, 4):
                circ.cx(i, j)

        qc = apply_measurement(circ)
        circuits = [qc for i in range(3)]
        num_shots = int(1e6)

        backend = Aer.get_backend('qasm_simulator')
        backend_options = {'method': 'automatic', 'max_parallel_threads': 1, 'max_parallel_experiments': 1, 'max_parallel_shots': 1}
        serial_result = execute(circuits, backend, shots=num_shots, backend_options=backend_options).result()
        print(serial_result.metadata)

        backend = Aer.get_backend('qasm_simulator')
        backend_options = {'method': 'automatic', 'max_parallel_threads': 1, 'max_parallel_experiments': 3, 'max_parallel_shots': 1}
        parallel_result = execute(circuits, backend, shots=num_shots, backend_options=backend_options).result()
        print(parallel_result.metadata)

        # Los 3 circuitos deben ejecutarse en paralelo (más de 1 experimento a la vez)
        self.assertGreater(parallel_result.metadata['parallel_experiments'], 1)


if __name__ == '__main__':
    unittest.main(argv=[''])
