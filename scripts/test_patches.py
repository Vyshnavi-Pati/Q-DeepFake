from pathlib import Path
import sys

from PIL import Image

from app.config import (
    GRID_SIZE,
    MAIN_MODEL_PATH,
    MODEL_CONFIG_PATH,
    QUANTUM_MARKED,
    SPECIALIST_MODEL_PATH,
)
from app.services.patches import analyze_patches
from app.services.predictor import ForensicsPredictor


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.test_patches <image_path>")
        raise SystemExit(1)

    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        raise SystemExit(1)

    image = Image.open(image_path).convert("RGB")

    predictor = ForensicsPredictor(
        main_model_path=MAIN_MODEL_PATH,
        specialist_model_path=SPECIALIST_MODEL_PATH,
        config_path=MODEL_CONFIG_PATH,
    )

    result = analyze_patches(
        image=image,
        predictor=predictor,
        grid_size=GRID_SIZE,
        num_marked=QUANTUM_MARKED,
    )

    print("\n========================================")
    print("PATCH FORENSIC ANALYSIS")
    print("========================================")
    print(f"Total patches: {result['total_patches']}")
    print(f"Marked patches: {result['marked_indices']}")
    print("\nTop suspicious patches:")

    for patch in result["top_candidates"]:
        print(f"\nPatch {patch['index']}")
        print(f"  Grid position: row={patch['row']}, column={patch['column']}")
        print(f"  Bounding box: {patch['bbox']}")
        print(f"  Suspiciousness: {patch['suspiciousness'] * 100:.2f}%")
        print(f"  Prediction: {patch['predicted_class']}")


if __name__ == "__main__":
    main()
