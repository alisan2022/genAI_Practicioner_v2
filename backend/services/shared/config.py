from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(BACKEND_ENV_PATH)
load_dotenv()

TRIAGE_SERVICE_URL = os.getenv("TRIAGE_SERVICE_URL", "http://127.0.0.1:8001")
KNOWLEDGE_SERVICE_URL = os.getenv("KNOWLEDGE_SERVICE_URL", "http://127.0.0.1:8002")
FACILITY_SERVICE_URL = os.getenv("FACILITY_SERVICE_URL", "http://127.0.0.1:8003")
TRANSPORT_SERVICE_URL = os.getenv("TRANSPORT_SERVICE_URL", "http://127.0.0.1:8004")
CHAT_SERVICE_URL = os.getenv("CHAT_SERVICE_URL", "http://127.0.0.1:8005")

MEDICAL_LLM_API_KEY = (
    os.getenv("MEDICAL_LLM_API_KEY")
    or os.getenv("HF_TOKEN")
    or os.getenv("HUGGINGFACE_API_TOKEN")
    or os.getenv("OPENAI_API_KEY")
)
MEDICAL_LLM_BASE_URL = os.getenv("MEDICAL_LLM_BASE_URL") or os.getenv("HF_BASE_URL")
MEDICAL_LLM_MODEL = os.getenv("MEDICAL_LLM_MODEL", "").strip()
MEDICAL_LLM_ENABLED = bool(MEDICAL_LLM_API_KEY and MEDICAL_LLM_MODEL)

DEFAULT_RULES_MODEL_LABEL = "rules+ragnone"
DEFAULT_DISCLAIMER = (
    "Educational guidance only. This app does not diagnose illness. "
    "If symptoms are severe, sudden, or worsening, contact NHS 111 or call 999 immediately."
)
