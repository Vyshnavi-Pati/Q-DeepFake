import json
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from PIL import Image, ImageOps
from torchvision import transforms
from torchvision.models import convnext_tiny


class ForensicsPredictor:
    CLASS_NAMES = [
        "Completely Real",
        "Modified Using AI",
        "Completely AI Generated",
    ]

    SPECIALIST_NAMES = [
        "Completely Real",
        "Completely AI Generated",
    ]

    def __init__(
        self,
        main_model_path: Path,
        specialist_model_path: Path,
        config_path: Path,
    ):
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        with open(config_path, "r", encoding="utf-8") as file:
            self.config = json.load(file)

        self.alpha = float(
            self.config.get("ensemble_alpha", 0.40)
        )

        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

        # The two trained checkpoints use different classifier heads.
        self.main_model = self._build_main_model()
        self.specialist_model = self._build_specialist_model()

        self._load_weights(self.main_model, main_model_path)
        self._load_weights(self.specialist_model, specialist_model_path)

        self.main_model.to(self.device).eval()
        self.specialist_model.to(self.device).eval()

    @staticmethod
    def _build_main_model() -> nn.Module:
        # Matches the main Colab checkpoint:
        # classifier.1 = LayerNorm
        # classifier.3 = Linear(768, 3)
        model = convnext_tiny(weights=None)
        model.classifier = nn.Sequential(
            nn.Flatten(1),
            nn.LayerNorm(768),
            nn.GELU(),
            nn.Linear(768, 3),
        )
        return model

    @staticmethod
    def _build_specialist_model() -> nn.Module:
        # Matches the standard torchvision ConvNeXt checkpoint:
        # classifier.0 = LayerNorm
        # classifier.2 = Linear(768, 2)
        model = convnext_tiny(weights=None)
        model.classifier[2] = nn.Linear(
            model.classifier[2].in_features,
            2,
        )
        return model

    @staticmethod
    def _load_weights(model: nn.Module, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")

        try:
            state_dict = torch.load(
                path,
                map_location="cpu",
                weights_only=True,
            )
        except TypeError:
            state_dict = torch.load(path, map_location="cpu")

        model.load_state_dict(state_dict)

    @staticmethod
    def _prepare_image(image: Image.Image) -> Image.Image:
        image = ImageOps.exif_transpose(image)
        return image.convert("RGB")

    def _tensor_from_image(self, image: Image.Image) -> torch.Tensor:
        return self.transform(self._prepare_image(image))

    @torch.inference_mode()
    def main_probabilities(
        self,
        images: list[Image.Image],
    ) -> torch.Tensor:
        tensors = torch.stack([
            self._tensor_from_image(image)
            for image in images
        ])
        tensors = tensors.to(self.device, non_blocking=True)
        logits = self.main_model(tensors)
        return torch.softmax(logits, dim=1).cpu()

    @torch.inference_mode()
    def specialist_probabilities(
        self,
        image: Image.Image,
    ) -> torch.Tensor:
        tensor = self._tensor_from_image(image)
        tensor = tensor.unsqueeze(0).to(self.device, non_blocking=True)
        logits = self.specialist_model(tensor)
        return torch.softmax(logits, dim=1)[0].cpu()

    def predict_classical(self, image: Image.Image) -> dict[str, Any]:
        image = self._prepare_image(image)
        main_prob = self.main_probabilities([image])[0].numpy()
        main_prediction = int(main_prob.argmax())
        final_prob = main_prob.copy()

        # The main model controls routing. No ground-truth label is used.
        if main_prediction in (0, 2):
            specialist_prob = self.specialist_probabilities(image).numpy()

            p_real = float(main_prob[0])
            p_modified = float(main_prob[1])
            p_ai = float(main_prob[2])
            non_modified = p_real + p_ai

            if non_modified > 1e-8:
                main_real = p_real / non_modified
                main_ai = p_ai / non_modified

                specialist_real = float(specialist_prob[0])
                specialist_ai = float(specialist_prob[1])

                blended_real = (
                    (1.0 - self.alpha) * main_real
                    + self.alpha * specialist_real
                )
                blended_ai = (
                    (1.0 - self.alpha) * main_ai
                    + self.alpha * specialist_ai
                )

                final_prob[0] = non_modified * blended_real
                final_prob[1] = p_modified
                final_prob[2] = non_modified * blended_ai

        final_prediction = int(final_prob.argmax())

        return {
            "probabilities": {
                "completely_real": float(final_prob[0]),
                "modified_using_ai": float(final_prob[1]),
                "completely_ai_generated": float(final_prob[2]),
            },
            "classification": self.CLASS_NAMES[final_prediction],
            "main_prediction": self.CLASS_NAMES[main_prediction],
            "ensemble_alpha": self.alpha,
            "device": str(self.device),
        }

    def predict(self, image: Image.Image) -> dict[str, Any]:
        result = self.predict_classical(image)
        result["percentages"] = {
            key: round(value * 100.0, 2)
            for key, value in result["probabilities"].items()
        }
        return result
