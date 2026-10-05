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
from app.services.quantum import simulate_grover_search_all

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
        "message": (
            "Deep Fake | Quantum Image Forensics API"
        ),
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "device": str(
            predictor.device
        ),
        "quantum_enabled": (
            QUANTUM_ENABLED
        ),
    }


@app.post("/predict")
async def predict_image(
    file: UploadFile = File(...)
):

    # --------------------------------------------------------
    # FILE VALIDATION
    # --------------------------------------------------------

    if (
        not file.content_type
        or not file.content_type.startswith("image/")
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Please upload a PNG, JPG, "
                "or JPEG image."
            ),
        )

    contents = await file.read()

    if not contents:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    try:

        image = Image.open(
            BytesIO(contents)
        ).convert("RGB")

    except UnidentifiedImageError as exc:

        raise HTTPException(
            status_code=400,
            detail=(
                "The uploaded file is not "
                "a valid image."
            ),
        ) from exc


    # ========================================================
    # CLASSICAL AI ANALYSIS
    # ========================================================

    classical_result = predictor.predict(
        image
    )

    response = {
        "filename": file.filename,

        "classification": (
            classical_result[
                "classification"
            ]
        ),

        "probabilities": (
            classical_result[
                "probabilities"
            ]
        ),

        "percentages": (
            classical_result[
                "percentages"
            ]
        ),

        "model": {
            "main_prediction": (
                classical_result[
                    "main_prediction"
                ]
            ),

            "ensemble_alpha": (
                classical_result[
                    "ensemble_alpha"
                ]
            ),

            "device": (
                classical_result[
                    "device"
                ]
            ),
        },
    }


    # ========================================================
    # QUANTUM ANALYSIS
    # ========================================================

    if QUANTUM_ENABLED:

    # ========================================================
    # CLASSICAL PATCH ANALYSIS
    # ========================================================

        patch_analysis = analyze_patches(
            image=image,
            predictor=predictor,
            grid_size=GRID_SIZE,
            suspicion_threshold=0.40,
        )

        marked_indices = (
            patch_analysis[
                "marked_indices"
            ]
        )

        # ========================================================
        # GROVER SEARCH
        # ========================================================

        quantum_result = (
            simulate_grover_search_all(
                marked_indices=marked_indices,
                num_items=GRID_SIZE * GRID_SIZE,
                shots=QUANTUM_SHOTS,
            )
            if marked_indices
            else {
                "num_items": GRID_SIZE * GRID_SIZE,
                "num_qubits": int(
                    (GRID_SIZE * GRID_SIZE)
                    .bit_length()
                    - 1
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
        )

        selected_indices = (
            quantum_result[
                "found_indices"
            ]
        )

        selected_patches = [
            patch
            for patch in patch_analysis[
                "patches"
            ]
            if patch["index"]
            in selected_indices
        ]

        selected_patch = next(
            (
                patch
                for patch in patch_analysis[
                    "patches"
                ]
                if patch["index"]
                == quantum_result[
                    "selected_index"
                ]
            ),
            None,
        )

        first_round = (
            quantum_result[
                "grover_rounds"
            ][0]
            if quantum_result[
                "grover_rounds"
            ]
            else None
        )

        response[
            "quantum_analysis"
        ] = {

            "enabled": True,

            "algorithm": "Grover Search",

            "search_mode": (
                "Multi-target suspicious-patch search"
            ),

            "grid_size": GRID_SIZE,

            "search_space_size": (
                quantum_result[
                    "num_items"
                ]
            ),

            "qubits": (
                quantum_result[
                    "num_qubits"
                ]
            ),

            "suspicion_threshold": (
                patch_analysis[
                    "suspicion_threshold"
                ]
            ),

            "marked_indices": (
                patch_analysis[
                    "marked_indices"
                ]
            ),

            "marked_count": (
                patch_analysis[
                    "marked_count"
                ]
            ),

            "patch_coverage": (
                patch_analysis[
                    "patch_coverage"
                ]
            ),

            "found_indices": (
                selected_indices
            ),

            "found_count": (
                quantum_result[
                    "total_found"
                ]
            ),

            "selected_patch_indices": (
                selected_indices
            ),

            "selected_patch_index": (
                quantum_result[
                    "selected_index"
                ]
            ),

            "selected_bitstring": (
                quantum_result[
                    "selected_bitstring"
                ]
            ),

            "selected_patch_is_marked": (
                quantum_result[
                    "selected_is_marked"
                ]
            ),

            "selected_patch": (
                selected_patch
            ),

            "selected_patches": (
                selected_patches
            ),

            "grover_iterations": (
                first_round[
                    "grover_iterations"
                ]
                if first_round
                else 0
            ),

            "search_rounds": (
                quantum_result[
                    "grover_rounds"
                ]
            ),

            "measurement_counts": (
                quantum_result[
                    "counts"
                ]
            ),

            "circuit_depth": (
                quantum_result[
                    "circuit_depth"
                ]
            ),

            "top_candidates": (
                patch_analysis[
                    "top_candidates"
                ]
            ),

            "patches": (
                patch_analysis[
                    "patches"
                ]
            ),

            "note": (
                "Every image patch is scored classically. "
                "A patch becomes a quantum target when its "
                "non-real probability reaches the forensic "
                "threshold. Grover then searches the complete "
                "16-patch space for the marked states. When "
                "multiple patches are marked, the search is "
                "repeated to recover the remaining marked "
                "patches. Grover does not change the image "
                "classification probabilities."
            ),
        }

    else:

        response[
            "quantum_analysis"
        ] = {
            "enabled": False
        }


    return response