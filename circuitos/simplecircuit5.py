from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

qc = QuantumCircuit(2, 2)
qc.x(0)
qc.cx(0, 1)
qc.cx(1, 0)
qc.cx(0, 1)
qc.measure([0, 1], [1, 0])

sim = AerSimulator()
job = sim.run(qc, shots=100)
result = job.result()
counts = result.get_counts()

print("\nResultados de la medición:")
print(counts)
