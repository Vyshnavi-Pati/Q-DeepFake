import argparse
import os

from dotenv import load_dotenv
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime.executor_sampler import Sampler

from app.services.quantum import build_grover_circuit


def get_counts(pub_result):
    data = pub_result.data

    for register_name in ["c", "cr", "meas"]:
        if hasattr(data, register_name):
            register = getattr(data, register_name)
            if hasattr(register, "get_counts"):
                return register.get_counts()

    raise RuntimeError("Could not find measurement counts in IBM Quantum result.")


def main():
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default=os.getenv("IBM_BACKEND", ""))
    parser.add_argument("--shots", type=int, default=1024)
    args = parser.parse_args()

    token = os.getenv("IBM_TOKEN", "")
    channel = os.getenv("IBM_CHANNEL", "ibm_quantum_platform")
    instance = os.getenv("IBM_INSTANCE", "")

    print("=" * 60)
    print("IBM QUANTUM GROVER HARDWARE DEMO")
    print("=" * 60)

    if token:
        service_kwargs = {
            "channel": channel,
            "token": token,
        }
        if instance:
            service_kwargs["instance"] = instance
        service = QiskitRuntimeService(**service_kwargs)
    else:
        service = QiskitRuntimeService()

    if args.backend:
        backend = service.backend(args.backend)
    else:
        backend = service.least_busy(
            min_num_qubits=4,
            operational=True,
            simulator=False,
        )

    print(f"Backend: {backend.name}")

    marked_indices = [2, 5, 9, 13]
    circuit = build_grover_circuit(
        num_items=16,
        marked_indices=marked_indices,
    )

    print("\nOriginal circuit:")
    print(circuit.draw())

    pass_manager = generate_preset_pass_manager(
        backend=backend,
        optimization_level=1,
    )
    isa_circuit = pass_manager.run(circuit)

    print(f"\nTranspiled depth: {isa_circuit.depth()}")
    print("\nSubmitting to IBM Quantum...")

    sampler = Sampler(mode=backend)
    job = sampler.run([isa_circuit], shots=args.shots)

    print(f"Job ID: {job.job_id()}")
    result = job.result()
    counts = get_counts(result[0])

    print("\nMeasurement counts:")
    print(counts)

    selected_bitstring = max(counts, key=counts.get)
    selected_index = int(selected_bitstring.replace(" ", ""), 2)

    print(f"\nSelected index: {selected_index}")
    print("Is marked:", selected_index in marked_indices)
    print("\nIBM Quantum hardware demo complete.")


if __name__ == "__main__":
    main()
