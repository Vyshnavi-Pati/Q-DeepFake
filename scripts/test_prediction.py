from pathlib import Path
import sys

from PIL import Image

from app.config import MAIN_MODEL_PATH, MODEL_CONFIG_PATH, SPECIALIST_MODEL_PATH
from app.services.predictor import ForensicsPredictor


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.test_prediction <image_path>")
        raise SystemExit(1)

    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        raise SystemExit(1)

    image = Image.open(image_path)

    predictor = ForensicsPredictor(
        main_model_path=MAIN_MODEL_PATH,
        specialist_model_path=SPECIALIST_MODEL_PATH,
        config_path=MODEL_CONFIG_PATH,
    )

    result = predictor.predict(image)

    print("\n========================================")
    print("IMAGE FORENSICS PREDICTION")
    print("========================================")
    print(f"\nClassification: {result['classification']}")
    print("\nProbabilities:")
    for name, value in result["percentages"].items():
        print(f"  {name}: {value}%")
    print("\nModel information:")
    print(f"  Main prediction: {result['main_prediction']}")
    print(f"  Ensemble alpha: {result['ensemble_alpha']}")
    print(f"  Device: {result['device']}")


if __name__ == "__main__":
    main()
