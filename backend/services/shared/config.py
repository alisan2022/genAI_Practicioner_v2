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

DEFAULT_TRIAGE_LLM_MODEL = "m42-health/Llama3-Med42-8B"
DEFAULT_TRIAGE_LLM_BASE_URL = "https://router.huggingface.co/featherless-ai/v1"
TRIAGE_LLM_API_KEY = os.getenv("TRIAGE_LLM_API_KEY") or MEDICAL_LLM_API_KEY
TRIAGE_LLM_BASE_URL = (
    os.getenv("TRIAGE_LLM_BASE_URL")
    or DEFAULT_TRIAGE_LLM_BASE_URL
)
TRIAGE_LLM_MODEL = (
    os.getenv("TRIAGE_LLM_MODEL", DEFAULT_TRIAGE_LLM_MODEL).strip()
    or DEFAULT_TRIAGE_LLM_MODEL
)
TRIAGE_LLM_ENABLED = bool(TRIAGE_LLM_API_KEY)

DEFAULT_CHAT_LLM_MODEL = "Qwen/Qwen2.5-72B-Instruct:fastest"
DEFAULT_CHAT_LLM_BASE_URL = "https://router.huggingface.co/v1"
CHAT_LLM_API_KEY = os.getenv("CHAT_LLM_API_KEY") or MEDICAL_LLM_API_KEY
CHAT_LLM_BASE_URL = os.getenv("CHAT_LLM_BASE_URL") or DEFAULT_CHAT_LLM_BASE_URL
CHAT_LLM_MODEL = (
    os.getenv("CHAT_LLM_MODEL", DEFAULT_CHAT_LLM_MODEL).strip()
    or DEFAULT_CHAT_LLM_MODEL
)
CHAT_LLM_ENABLED = bool(CHAT_LLM_API_KEY)

DEFAULT_SAFETY_MODEL_LABEL = "safety-guardrails"
DEFAULT_DISCLAIMER = (
    "Educational guidance only. This app does not diagnose illness. "
    "If symptoms are severe, sudden, or worsening, contact NHS 111 or call 999 immediately."
)
