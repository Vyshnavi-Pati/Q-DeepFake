import math
from typing import Any

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit_aer import AerSimulator


def _apply_phase_flip(circuit: QuantumCircuit, marked_index: int) -> None:
    num_qubits = circuit.num_qubits
    binary = format(marked_index, f"0{num_qubits}b")

    for qubit in range(num_qubits):
        bit = binary[num_qubits - 1 - qubit]
        if bit == "0":
            circuit.x(qubit)

    target = num_qubits - 1
    controls = list(range(num_qubits - 1))
    circuit.h(target)
    circuit.mcx(controls, target)
    circuit.h(target)

    for qubit in range(num_qubits):
        bit = binary[num_qubits - 1 - qubit]
        if bit == "0":
            circuit.x(qubit)


def _apply_oracle(circuit: QuantumCircuit, marked_indices: list[int]) -> None:
    for index in marked_indices:
        _apply_phase_flip(circuit, index)


def _apply_diffusion(circuit: QuantumCircuit) -> None:
    num_qubits = circuit.num_qubits
    circuit.h(range(num_qubits))
    circuit.x(range(num_qubits))

    target = num_qubits - 1
    controls = list(range(num_qubits - 1))
    circuit.h(target)
    circuit.mcx(controls, target)
    circuit.h(target)

    circuit.x(range(num_qubits))
    circuit.h(range(num_qubits))


def build_grover_circuit(
    num_items: int,
    marked_indices: list[int],
) -> QuantumCircuit:
    if num_items < 2 or (num_items & (num_items - 1)):
        raise ValueError("num_items must be a power of 2 and at least 2.")

    num_qubits = int(math.log2(num_items))
    marked_indices = sorted(set(marked_indices))

    if not marked_indices:
        raise ValueError("At least one marked index is required.")

    if any(index < 0 or index >= num_items for index in marked_indices):
        raise ValueError("A marked index is outside the search space.")

    qr = QuantumRegister(num_qubits, name="q")
    cr = ClassicalRegister(num_qubits, name="c")
    circuit = QuantumCircuit(qr, cr, name="grover_forensics")

    circuit.h(qr)

    iterations = max(
        1,
        int(math.floor((math.pi / 4) * math.sqrt(num_items / len(marked_indices)))),
    )

    for _ in range(iterations):
        _apply_oracle(circuit, marked_indices)
        _apply_diffusion(circuit)

    circuit.measure(qr, cr)
    circuit.metadata = {
        "num_items": num_items,
        "marked_indices": marked_indices,
        "grover_iterations": iterations,
    }
    return circuit


def simulate_grover_search(
    marked_indices: list[int],
    num_items: int = 16,
    shots: int = 512,
    seed: int = 42,
) -> dict[str, Any]:
    circuit = build_grover_circuit(
        num_items=num_items,
        marked_indices=marked_indices,
    )

    simulator = AerSimulator(seed_simulator=seed)
    result = simulator.run(circuit, shots=shots).result()
    counts = result.get_counts()

    selected_bitstring = max(counts, key=counts.get)
    selected_index = int(selected_bitstring.replace(" ", ""), 2)
    metadata = circuit.metadata or {}

    return {
        "num_items": num_items,
        "num_qubits": circuit.num_qubits,
        "marked_indices": marked_indices,
        "grover_iterations": metadata.get("grover_iterations", 0),
        "shots": shots,
        "counts": counts,
        "selected_bitstring": selected_bitstring,
        "selected_index": selected_index,
        "selected_is_marked": selected_index in marked_indices,
        "circuit_depth": circuit.depth(),
        "circuit": circuit,
    }
