from io import BytesIO

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError

from app.config import (
    GRID_SIZE,
    MAIN_MODEL_PATH,
    MODEL_CONFIG_PATH,
    QUANTUM_ENABLED,
    QUANTUM_MARKED,
    QUANTUM_SHOTS,
    SPECIALIST_MODEL_PATH,
)
from app.services.patches import analyze_patches
from app.services.predictor import ForensicsPredictor
from app.services.quantum import simulate_grover_search


app = FastAPI(
    title="Deep Fake | Quantum Image Forensics API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor = ForensicsPredictor(
    main_model_path=MAIN_MODEL_PATH,
    specialist_model_path=SPECIALIST_MODEL_PATH,
    config_path=MODEL_CONFIG_PATH,
)


@app.get("/")
def root():
    return {
        "message": "Deep Fake | Quantum Image Forensics API",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "device": str(predictor.device),
        "quantum_enabled": QUANTUM_ENABLED,
    }


@app.post("/predict")
async def predict_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PNG, JPG, or JPEG image.",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    try:
        image = Image.open(BytesIO(contents)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid image.",
        ) from exc

    classical_result = predictor.predict(image)

    response = {
        "filename": file.filename,
        "classification": classical_result["classification"],
        "probabilities": classical_result["probabilities"],
        "percentages": classical_result["percentages"],
        "model": {
            "main_prediction": classical_result["main_prediction"],
            "ensemble_alpha": classical_result["ensemble_alpha"],
            "device": classical_result["device"],
        },
    }

    if QUANTUM_ENABLED:
        patch_analysis = analyze_patches(
            image=image,
            predictor=predictor,
            grid_size=GRID_SIZE,
            num_marked=QUANTUM_MARKED,
        )

        quantum_result = simulate_grover_search(
            marked_indices=patch_analysis["marked_indices"],
            num_items=GRID_SIZE * GRID_SIZE,
            shots=QUANTUM_SHOTS,
        )

        selected_index = quantum_result["selected_index"]
        selected_patch = next(
            (
                item
                for item in patch_analysis["patches"]
                if item["index"] == selected_index
            ),
            None,
        )

        response["quantum_analysis"] = {
            "algorithm": "Grover Search",
            "search_space_size": quantum_result["num_items"],
            "qubits": quantum_result["num_qubits"],
            "marked_indices": quantum_result["marked_indices"],
            "grover_iterations": quantum_result["grover_iterations"],
            "selected_patch_index": selected_index,
            "selected_patch_is_marked": quantum_result["selected_is_marked"],
            "selected_patch": selected_patch,
            "measurement_counts": quantum_result["counts"],
            "circuit_depth": quantum_result["circuit_depth"],
            "top_candidates": patch_analysis["top_candidates"],
            "note": (
                "Grover searches the classically scored candidate patch space. "
                "It does not change the ML classification probabilities."
            ),
        }
    else:
        response["quantum_analysis"] = {"enabled": False}

    return response
