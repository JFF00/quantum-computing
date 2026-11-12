from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram

qc = QuantumCircuit(1, 1)
qc.x(0)
qc.measure(0, 0)
simulator = AerSimulator()

job = simulator.run(qc, shots=1000)
result = job.result()
counts = result.get_counts()

print("\nResultados de la medición (Shots = 1000):")
print(counts)
