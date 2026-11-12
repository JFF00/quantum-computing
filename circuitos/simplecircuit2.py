from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram

qc = QuantumCircuit(1, 1)
qc.h(0)
qc.measure(0, 0)

sim = AerSimulator()

job = sim.run(qc, shots=100)
result = job.result()
count = result.get_counts()

print("\nResultados de la medición (Shots = 1000):")
print(count)
