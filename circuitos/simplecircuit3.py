from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

qc = QuantumCircuit(1, 1)
qc.h(0)
qc.z(0)
qc.h(0)
qc.measure(0, 0)

sim = AerSimulator()

job = sim.run(qc, shots=100)
result = job.result()
count = result.get_counts()
print("\nResultados de la medición:")
print(count)
