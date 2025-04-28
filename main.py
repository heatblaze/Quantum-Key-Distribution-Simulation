import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QProgressBar, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Function to simulate the QKD protocol
def simulate_qkd(num_qubits):
    alice_bases = random.choices([0, 1], k=num_qubits)
    alice_bits = random.choices([0, 1], k=num_qubits)

    alice_qubits = []
    for i in range(num_qubits):
        circuit = QuantumCircuit(1, 1)
        if alice_bases[i] == 0:
            circuit.h(0)
        if alice_bits[i] == 1:
            circuit.x(0)
        circuit.measure(0, 0)

        simulator = AerSimulator()
        compiled_circuit = transpile(circuit, simulator)
        job = simulator.run(compiled_circuit, shots=1)
        result = job.result()
        counts = result.get_counts(compiled_circuit)
        alice_qubits.append(int(max(counts, key=counts.get)))

    bob_bases = random.choices([0, 1], k=num_qubits)
    bob_bits = measure_qubits(alice_qubits, bob_bases)

    shared_key = []
    for i in range(num_qubits):
        if alice_bases[i] == bob_bases[i]:
            shared_key.append(alice_bits[i])

    return alice_qubits, bob_bits, shared_key

def measure_qubits(qubits, bases):
    measured_bits = []
    backend = AerSimulator()

    for qubit, basis in zip(qubits, bases):
        circuit = QuantumCircuit(1, 1)
        if basis == 0:
            circuit.h(0)
        circuit.measure(0, 0)

        compiled_circuit = transpile(circuit, backend)
        job = backend.run(compiled_circuit, shots=1)
        result = job.result()
        counts = result.get_counts(compiled_circuit)
        bit = int(max(counts, key=counts.get))
        measured_bits.append(bit)

    return measured_bits

# PyQt5 GUI for displaying the quantum circuit and results
class QKDApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quantum Key Distribution Simulation")
        self.setGeometry(100, 100, 700, 700)

        # Dark Theme Style
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: white;
            }
            QPushButton {
                background-color: #444444;
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QLabel {
                color: white;
                font-size: 14px;
                padding: 5px;
            }
            QProgressBar {
                background-color: #444444;
                color: white;
                border-radius: 5px;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #69c0ff;
            }
        """)

        # Main Layout
        self.layout = QVBoxLayout()

        # Title Label
        self.title_label = QLabel("Quantum Key Distribution Simulation", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 15px;")
        self.layout.addWidget(self.title_label)

        # Start Button
        self.start_button = QPushButton("Start Simulation", self)
        self.start_button.clicked.connect(self.start_simulation)
        self.layout.addWidget(self.start_button)

        # Spacer between buttons and results
        self.layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Quantum Circuit Visualization Label
        self.circuit_label = QLabel(self)
        self.layout.addWidget(self.circuit_label)

        # Spacer between the quantum circuit and results
        self.layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # Indeterminate mode
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)

        # Results Display
        self.result_label = QLabel("Results will be displayed here.", self)
        self.result_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.result_label)

        # Shared Key Display
        self.shared_key_label = QLabel("Shared Key: ", self)
        self.shared_key_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.shared_key_label)

        self.setLayout(self.layout)

    def start_simulation(self):
        # Disable the start button and show progress bar while simulation is running
        self.start_button.setEnabled(False)
        self.progress_bar.setVisible(True)

        # Create and start the worker thread for simulation
        self.worker = QKDWorker()
        self.worker.result_signal.connect(self.handle_simulation_results)
        self.worker.start()

    def handle_simulation_results(self, alice_qubits, bob_bits, shared_key):
        # Show the quantum circuit visualization
        num_qubits = len(alice_qubits)
        circuit = self.create_qkd_circuit(num_qubits)
        self.display_quantum_circuit(circuit)

        # Show results
        self.result_label.setText(f"Alice's qubits: {alice_qubits}\nBob's bits: {bob_bits}")
        self.shared_key_label.setText(f"Shared Key: {shared_key}")

        # Enable start button and hide progress bar
        self.start_button.setEnabled(True)
        self.progress_bar.setVisible(False)

    def create_qkd_circuit(self, num_qubits):
        """Create a simple quantum circuit for QKD simulation."""
        circuit = QuantumCircuit(num_qubits, num_qubits)

        # Apply Hadamard gate to each qubit to create superposition
        for qubit in range(num_qubits):
            circuit.h(qubit)

        # Add measurement operations
        circuit.measure(range(num_qubits), range(num_qubits))

        return circuit

    def display_quantum_circuit(self, circuit):
        """Display the quantum circuit diagram in the QLabel."""
        # Save the quantum circuit diagram to a file
        circuit.draw('mpl', filename='circuit.png')

        # Show the quantum circuit diagram on the QLabel
        pixmap = QPixmap('circuit.png')
        self.circuit_label.setPixmap(pixmap.scaled(500, 300, Qt.KeepAspectRatio))
        self.circuit_label.setAlignment(Qt.AlignCenter)

class QKDWorker(QThread):
    result_signal = pyqtSignal(list, list, list)

    def run(self):
        num_qubits = 5  # Example: Number of qubits
        alice_qubits, bob_bits, shared_key = simulate_qkd(num_qubits)
        print(f"Simulation Complete: Alice's qubits: {alice_qubits}, Bob's bits: {bob_bits}, Shared Key: {shared_key}")  # Debug print
        self.result_signal.emit(alice_qubits, bob_bits, shared_key)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QKDApp()
    window.show()
    sys.exit(app.exec_())
