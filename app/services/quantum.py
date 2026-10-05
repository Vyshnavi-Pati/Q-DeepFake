import math
from typing import Any

from qiskit import (
    ClassicalRegister,
    QuantumCircuit,
    QuantumRegister,
)

from qiskit_aer import AerSimulator


# ============================================================
# PHASE FLIP FOR ONE BASIS STATE
# ============================================================

def _apply_phase_flip(
    circuit: QuantumCircuit,
    marked_index: int,
) -> None:

    num_qubits = circuit.num_qubits

    binary = format(
        marked_index,
        f"0{num_qubits}b",
    )

    for qubit in range(num_qubits):

        bit = binary[
            num_qubits - 1 - qubit
        ]

        if bit == "0":
            circuit.x(qubit)

    target = num_qubits - 1

    controls = list(
        range(num_qubits - 1)
    )

    circuit.h(target)

    circuit.mcx(
        controls,
        target,
    )

    circuit.h(target)

    for qubit in range(num_qubits):

        bit = binary[
            num_qubits - 1 - qubit
        ]

        if bit == "0":
            circuit.x(qubit)


# ============================================================
# ORACLE
# ============================================================

def _apply_oracle(
    circuit: QuantumCircuit,
    marked_indices: list[int],
) -> None:

    for index in marked_indices:

        _apply_phase_flip(
            circuit,
            index,
        )


# ============================================================
# DIFFUSION
# ============================================================

def _apply_diffusion(
    circuit: QuantumCircuit,
) -> None:

    num_qubits = circuit.num_qubits

    circuit.h(
        range(num_qubits)
    )

    circuit.x(
        range(num_qubits)
    )

    target = num_qubits - 1

    controls = list(
        range(num_qubits - 1)
    )

    circuit.h(target)

    circuit.mcx(
        controls,
        target,
    )

    circuit.h(target)

    circuit.x(
        range(num_qubits)
    )

    circuit.h(
        range(num_qubits)
    )


# ============================================================
# CALCULATE OPTIMAL INTEGER GROVER ITERATIONS
# ============================================================

def _optimal_iterations(
    num_items: int,
    num_marked: int,
) -> int:

    if num_marked <= 0:
        return 0

    if num_marked >= num_items:
        return 0

    theta = math.asin(
        math.sqrt(
            num_marked / num_items
        )
    )

    iterations = round(
        math.pi /
        (4.0 * theta)
        - 0.5
    )

    return max(
        0,
        iterations
    )


# ============================================================
# BUILD GROVER CIRCUIT
# ============================================================

def build_grover_circuit(
    num_items: int,
    marked_indices: list[int],
) -> QuantumCircuit:

    if (
        num_items < 2
        or (
            num_items
            & (num_items - 1)
        )
    ):

        raise ValueError(
            "num_items must be a power of 2 and at least 2."
        )

    num_qubits = int(
        math.log2(num_items)
    )

    marked_indices = sorted(
        set(marked_indices)
    )

    if not marked_indices:

        raise ValueError(
            "At least one marked index is required."
        )

    if any(
        index < 0
        or index >= num_items
        for index in marked_indices
    ):

        raise ValueError(
            "A marked index is outside the search space."
        )

    qr = QuantumRegister(
        num_qubits,
        name="q",
    )

    cr = ClassicalRegister(
        num_qubits,
        name="c",
    )

    circuit = QuantumCircuit(
        qr,
        cr,
        name="grover_forensics",
    )

    # --------------------------------------------------------
    # SUPERPOSITION
    # --------------------------------------------------------

    circuit.h(qr)

    # --------------------------------------------------------
    # NUMBER OF ITERATIONS DEPENDS ON M
    # --------------------------------------------------------

    iterations = _optimal_iterations(
        num_items,
        len(marked_indices),
    )

    # --------------------------------------------------------
    # GROVER ITERATIONS
    # --------------------------------------------------------

    for _ in range(iterations):

        _apply_oracle(
            circuit,
            marked_indices,
        )

        _apply_diffusion(
            circuit
        )

    # --------------------------------------------------------
    # MEASUREMENT
    # --------------------------------------------------------

    circuit.measure(
        qr,
        cr,
    )

    circuit.metadata = {
        "num_items": num_items,
        "marked_indices": marked_indices,
        "grover_iterations": iterations,
    }

    return circuit


# ============================================================
# RUN ONE GROVER SEARCH
# ============================================================

def _run_single_search(
    marked_indices: list[int],
    num_items: int,
    shots: int,
    seed: int,
) -> dict[str, Any]:

    circuit = build_grover_circuit(
        num_items=num_items,
        marked_indices=marked_indices,
    )

    simulator = AerSimulator(
        seed_simulator=seed
    )

    result = simulator.run(
        circuit,
        shots=shots,
    ).result()

    counts = result.get_counts()

    selected_bitstring = max(
        counts,
        key=counts.get,
    )

    selected_index = int(
        selected_bitstring.replace(
            " ",
            "",
        ),
        2,
    )

    metadata = (
        circuit.metadata or {}
    )

    return {
        "num_items": num_items,

        "num_qubits": (
            circuit.num_qubits
        ),

        "marked_indices": (
            marked_indices
        ),

        "grover_iterations": (
            metadata.get(
                "grover_iterations",
                0,
            )
        ),

        "shots": shots,

        "counts": counts,

        "selected_bitstring": (
            selected_bitstring
        ),

        "selected_index": (
            selected_index
        ),

        "selected_is_marked": (
            selected_index
            in marked_indices
        ),

        "circuit_depth": (
            circuit.depth()
        ),

        "circuit": circuit,
    }


# ============================================================
# SEARCH FOR ALL MARKED PATCHES
# ============================================================

def simulate_grover_search_all(
    marked_indices: list[int],
    num_items: int = 16,
    shots: int = 512,
    seed: int = 42,
) -> dict[str, Any]:

    remaining = sorted(
        set(marked_indices)
    )

    original_marked = remaining.copy()

    found_indices = []

    rounds = []

    total_depth = 0

    # --------------------------------------------------------
    # NO SUSPICIOUS PATCHES
    # --------------------------------------------------------

    if not remaining:

        return {
            "num_items": num_items,

            "num_qubits": int(
                math.log2(num_items)
            ),

            "marked_indices": [],

            "found_indices": [],

            "grover_rounds": [],

            "total_found": 0,

            "selected_index": None,

            "selected_bitstring": None,

            "selected_is_marked": False,

            "counts": {},

            "circuit_depth": 0,

            "circuit": None,
        }

    # --------------------------------------------------------
    # ITERATIVELY FIND MARKED STATES
    # --------------------------------------------------------

    round_number = 1

    while remaining:

        selected_result = None

        # Retry because measurement is probabilistic.
        for attempt in range(5):

            candidate = _run_single_search(
                marked_indices=remaining,
                num_items=num_items,
                shots=shots,
                seed=(
                    seed
                    + round_number * 100
                    + attempt
                ),
            )

            if candidate[
                "selected_is_marked"
            ]:

                selected_result = candidate

                break

        # If a valid marked state was not obtained,
        # stop rather than pretending success.
        if selected_result is None:
            break

        selected_index = (
            selected_result[
                "selected_index"
            ]
        )

        found_indices.append(
            selected_index
        )

        remaining.remove(
            selected_index
        )

        total_depth += (
            selected_result[
                "circuit_depth"
            ]
        )

        rounds.append({
            "round": round_number,

            "marked_indices": (
                selected_result[
                    "marked_indices"
                ]
            ),

            "selected_index": (
                selected_index
            ),

            "selected_bitstring": (
                selected_result[
                    "selected_bitstring"
                ]
            ),

            "grover_iterations": (
                selected_result[
                    "grover_iterations"
                ]
            ),

            "shots": (
                selected_result[
                    "shots"
                ]
            ),

            "counts": (
                selected_result[
                    "counts"
                ]
            ),

            "circuit_depth": (
                selected_result[
                    "circuit_depth"
                ]
            ),
        })

        round_number += 1

    first_round = (
        rounds[0]
        if rounds
        else None
    )

    return {
        "num_items": num_items,

        "num_qubits": int(
            math.log2(num_items)
        ),

        "marked_indices": original_marked,

        "found_indices": found_indices,

        "grover_rounds": rounds,

        "total_found": len(
            found_indices
        ),

        "selected_index": (
            found_indices[0]
            if found_indices
            else None
        ),

        "selected_bitstring": (
            first_round[
                "selected_bitstring"
            ]
            if first_round
            else None
        ),

        "selected_is_marked": (
            len(found_indices) > 0
        ),

        "counts": (
            first_round["counts"]
            if first_round
            else {}
        ),

        "circuit_depth": total_depth,

        "circuit": None,
    }


# ============================================================
# SINGLE SEARCH FUNCTION
# KEPT FOR COMPATIBILITY
# ============================================================

def simulate_grover_search(
    marked_indices: list[int],
    num_items: int = 16,
    shots: int = 512,
    seed: int = 42,
) -> dict[str, Any]:

    return _run_single_search(
        marked_indices=marked_indices,
        num_items=num_items,
        shots=shots,
        seed=seed,
    )