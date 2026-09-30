from typing import Any

import numpy as np
from PIL import Image

from app.services.predictor import ForensicsPredictor


def extract_grid_patches(
    image: Image.Image,
    grid_size: int = 4,
) -> list[dict[str, Any]]:
    image = image.convert("RGB")
    width, height = image.size
    patch_width = width // grid_size
    patch_height = height // grid_size
    patches = []
    index = 0

    for row in range(grid_size):
        for col in range(grid_size):
            left = col * patch_width
            top = row * patch_height
            right = width if col == grid_size - 1 else (col + 1) * patch_width
            bottom = height if row == grid_size - 1 else (row + 1) * patch_height

            patches.append({
                "index": index,
                "row": row,
                "column": col,
                "bbox": [left, top, right, bottom],
                "image": image.crop((left, top, right, bottom)),
            })
            index += 1

    return patches


def analyze_patches(
    image: Image.Image,
    predictor: ForensicsPredictor,
    grid_size: int = 4,
    num_marked: int = 4,
) -> dict[str, Any]:
    patches = extract_grid_patches(image, grid_size=grid_size)
    patch_images = [item["image"] for item in patches]
    probabilities = predictor.main_probabilities(patch_images).numpy()

    analysed = []

    for item, prob in zip(patches, probabilities):
        p_real = float(prob[0])
        p_modified = float(prob[1])
        p_ai = float(prob[2])
        suspiciousness = 1.0 - p_real
        patch_prediction = int(np.argmax(prob))

        analysed.append({
            "index": item["index"],
            "row": item["row"],
            "column": item["column"],
            "bbox": item["bbox"],
            "suspiciousness": suspiciousness,
            "predicted_class": predictor.CLASS_NAMES[patch_prediction],
            "probabilities": {
                "completely_real": p_real,
                "modified_using_ai": p_modified,
                "completely_ai_generated": p_ai,
            },
        })

    analysed.sort(
        key=lambda item: item["suspiciousness"],
        reverse=True,
    )

    marked = analysed[:min(num_marked, len(analysed))]

    return {
        "total_patches": len(analysed),
        "marked_indices": [item["index"] for item in marked],
        "patches": analysed,
        "top_candidates": marked,
    }
