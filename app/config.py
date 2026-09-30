import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = PROJECT_ROOT / "artifacts"

MAIN_MODEL_PATH = ARTIFACT_DIR / "convnext_main.pt"
SPECIALIST_MODEL_PATH = ARTIFACT_DIR / "convnext_specialist.pt"
MODEL_CONFIG_PATH = ARTIFACT_DIR / "model_config.json"

load_dotenv(PROJECT_ROOT / ".env")

IMAGE_SIZE = int(os.getenv("IMAGE_SIZE", "224"))
GRID_SIZE = int(os.getenv("GRID_SIZE", "4"))
QUANTUM_ENABLED = os.getenv("QUANTUM_ENABLED", "true").lower() == "true"
QUANTUM_SHOTS = int(os.getenv("QUANTUM_SHOTS", "512"))
QUANTUM_MARKED = int(os.getenv("QUANTUM_MARKED", "4"))

IBM_BACKEND = os.getenv("IBM_BACKEND", "")
IBM_CHANNEL = os.getenv("IBM_CHANNEL", "ibm_quantum_platform")
IBM_TOKEN = os.getenv("IBM_TOKEN", "")
IBM_INSTANCE = os.getenv("IBM_INSTANCE", "")
