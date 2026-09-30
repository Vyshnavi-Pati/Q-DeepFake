import json
from pathlib import Path

from app.services.quantum import simulate_grover_search


def main():
    marked_indices = [2, 5, 9, 13]

    result = simulate_grover_search(
        marked_indices=marked_indices,
        num_items=16,
        shots=1024,
    )

    print("=" * 50)
    print("GROVER QUANTUM SIMULATION")
    print("=" * 50)
    print(f"Search space      : {result['num_items']}")
    print(f"Qubits             : {result['num_qubits']}")
    print(f"Marked indices     : {result['marked_indices']}")
    print(f"Grover iterations  : {result['grover_iterations']}")
    print(f"Selected index     : {result['selected_index']}")
    print(f"Selected is marked : {result['selected_is_marked']}")
    print(f"Circuit depth      : {result['circuit_depth']}")
    print("\nMeasurement counts:")
    print(result["counts"])
    print("\nCircuit:")
    print(result["circuit"].draw())

    output_path = (
        Path(__file__).resolve().parents[1]
        / "artifacts"
        / "quantum_demo.json"
    )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            {key: value for key, value in result.items() if key != "circuit"},
            file,
            indent=2,
        )

    print(f"\nSaved result to: {output_path}")


if __name__ == "__main__":
    main()
