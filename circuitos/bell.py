from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 0], [0, 1])

sim = AerSimulator()
job = sim.run(qc, shots=100)
results = job.result()
count = results.get_counts()

print("\nResultados de la medición:")
print(count)
