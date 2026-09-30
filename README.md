# Deep Fake | Quantum Image Forensics

A hybrid classical-quantum prototype for image forensics with three output classes:

1. Completely Real
2. Modified Using AI
3. Completely AI Generated

## Project layout

- `app/` - FastAPI backend, model inference, patch analysis, and Grover search.
- `frontend/` - static HTML/CSS/JavaScript interface supplied by the project team and connected to the backend API.
- `artifacts/` - trained ConvNeXt checkpoints and a local quantum simulation result.
- `scripts/` - local prediction, patch-analysis, quantum-simulation, and IBM Quantum demonstration scripts.

## Machine-learning pipeline

The system loads two trained ConvNeXt-Tiny models:

- a 3-class main forensic classifier;
- a Real-vs-AI specialist used when the main model predicts Real or AI Generated.

The deployed blending factor is `alpha = 0.40`.

Measured on the 450-image held-out test set used for the project evaluation:

- Accuracy: 85.78%
- Macro-F1: 85.67%

These metrics describe the held-out evaluation set and are not a guarantee for arbitrary images from other sources.

## Quantum component

The image is divided into a 4x4 grid, giving a 16-state search space. The classical model scores the candidate patches and the top four are marked. Grover's algorithm is then used to search this candidate space.

The quantum analysis is separate from the ML probability output. It does not overwrite or claim to improve the measured classifier accuracy.

The included local simulation artifact records a 16-item, 4-qubit Grover experiment with marked indices `[2, 5, 9, 13]`.

## Run the backend

Create and activate the environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

Start FastAPI:

```bash
./run_backend.sh
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Run the frontend

In a second terminal:

```bash
./run_frontend.sh
```

Open:

`http://127.0.0.1:5500`

The frontend sends the selected image to:

`POST http://127.0.0.1:8000/predict`

## Local quantum simulation

```bash
source .venv/bin/activate
python -m scripts.simulate_quantum
```

## Test a model directly

```bash
python -m scripts.test_prediction /path/to/image.jpg
```

## IBM Quantum hardware demonstration

The IBM script uses the current client-side `Sampler` API from `qiskit-ibm-runtime 0.50.0`.

Add IBM credentials to a local `.env` file when hardware execution is available. Do not commit `.env`.

Then run:

```bash
python -m scripts.ibm_demo
```

A specific backend can be supplied with:

```bash
python -m scripts.ibm_demo --backend BACKEND_NAME
```

## Important technical limitation

Grover's algorithm provides a theoretical quadratic query-complexity advantage for unstructured search. This project does not claim an end-to-end wall-clock speedup for the complete image-forensics pipeline because the image scoring/oracle construction remains classical.

## Training data

The training dataset is not redistributed in this repository. Only the trained model artifacts needed for local inference are included.
