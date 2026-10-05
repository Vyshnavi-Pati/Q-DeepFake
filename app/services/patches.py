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

            right = (
                width
                if col == grid_size - 1
                else (col + 1) * patch_width
            )

            bottom = (
                height
                if row == grid_size - 1
                else (row + 1) * patch_height
            )

            patches.append({
                "index": index,
                "row": row,
                "column": col,
                "bbox": [
                    left,
                    top,
                    right,
                    bottom,
                ],
                "image": image.crop(
                    (
                        left,
                        top,
                        right,
                        bottom,
                    )
                ),
            })

            index += 1

    return patches


def analyze_patches(
    image: Image.Image,
    predictor: ForensicsPredictor,
    grid_size: int = 4,
    suspicion_threshold: float = 0.40,
) -> dict[str, Any]:

    patches = extract_grid_patches(
        image,
        grid_size=grid_size,
    )

    patch_images = [
        patch["image"]
        for patch in patches
    ]

    probabilities = (
        predictor
        .main_probabilities(
            patch_images
        )
        .numpy()
    )

    analysed = []

    # TRUE MODEL ORDER:
    #
    # 0 = Completely Real
    # 1 = Completely AI Generated
    # 2 = Modified Using AI

    for patch, prob in zip(
        patches,
        probabilities,
    ):

        p_real = float(
            prob[0]
        )

        p_ai = float(
            prob[1]
        )

        p_modified = float(
            prob[2]
        )

        # ----------------------------------------------------
        # FORENSIC SUSPICIOUSNESS
        #
        # Anything that is not classified as Real contributes
        # to suspiciousness.
        # ----------------------------------------------------

        suspiciousness = (
            p_ai + p_modified
        )

        # Equivalent to:
        #
        # suspiciousness = 1 - p_real

        patch_prediction = int(
            np.argmax(prob)
        )

        # ----------------------------------------------------
        # MARKING RULE
        #
        # A patch becomes a quantum target when its
        # non-real probability reaches the threshold.
        # ----------------------------------------------------

        marked = (
            suspiciousness
            >= suspicion_threshold
        )

        analysed.append({
            "index": patch["index"],
            "row": patch["row"],
            "column": patch["column"],
            "bbox": patch["bbox"],

            "suspiciousness": suspiciousness,

            "marked": marked,

            "predicted_class": (
                predictor.CLASS_NAMES[
                    patch_prediction
                ]
            ),

            "probabilities": {
                "completely_real": p_real,
                "completely_ai_generated": p_ai,
                "modified_using_ai": p_modified,
            },
        })

    # --------------------------------------------------------
    # RANKING IS ONLY FOR DISPLAY.
    #
    # IMPORTANT:
    # We DO NOT select top-4 anymore.
    # --------------------------------------------------------

    ranked_patches = sorted(
        analysed,
        key=lambda item: item["suspiciousness"],
        reverse=True,
    )

    marked_patches = [
        item
        for item in analysed
        if item["marked"]
    ]

    marked_indices = [
        item["index"]
        for item in marked_patches
    ]

    return {
        "total_patches": len(analysed),

        "grid_size": grid_size,

        "suspicion_threshold": (
            suspicion_threshold
        ),

        "marked_indices": marked_indices,

        "marked_count": len(
            marked_indices
        ),

        "patch_coverage": (
            len(marked_indices)
            / len(analysed)
            if analysed
            else 0.0
        ),

        "patches": analysed,

        "marked_patches": marked_patches,

        "top_candidates": ranked_patches[:4],
    }