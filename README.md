# GenAI Practitioner v2

GenAI Practitioner v2 is a clean rebuild of the Bournemouth health-triage prototype as a simpler, safer, store-ready mobile system.

## Things Reconsidered in Version 2

The original project already is strong :

- a Python microservices backend
- Bournemouth-specific facility recommendations
- transport suggestions
- an LLM orchestration flow
- two separate mobile clients (`Flutter` and `Expo`)

The main issues were architectural duplication and too much emphasis on the model for core decisioning. For coursework and demo safety, the new version keeps the same product idea but changes the implementation strategy:

- one mobile app instead of two
- deterministic triage logic first
- RAG-backed local knowledge retrieval second
- optional medical LLM refinement third

That means the app still feels intelligent, but it does not collapse if an external model is unavailable.

## v2 Architecture

```text
mobile-app (Expo / React Native)
        |
        v
gateway service
        |
        +--> triage service
        |      |
        |      +--> knowledge service (RAG)
        |      +--> facility service
        |      +--> transport service
        |
        +--> chat service
               |
               +--> knowledge service (RAG)
```

## Core Product Flow

1. The user enters symptoms, risk details, and optional location.
2. The triage service scores urgency with basic rule-based logic.
3. The service retrieves Bournemouth and NHS-style guidance through a lightweight RAG layer.
4. Facility and transport services return practical local recommendations.
5. If a medical LLM is configured, it only refines the wording of the response and follow-up chat. It does not own the core triage decision.

## Stack Choices

- Backend: Python + FastAPI
- Mobile: Expo + React Native + TypeScript
- Store packaging: EAS config included for Android/iOS builds
- RAG: lightweight local retrieval over curated Bournemouth knowledge cards
- LLM support: optional OpenAI-compatible endpoint for healthcare-tuned models

## Recommended Medical Models

The backend is intentionally model-agnostic. If you want a healthcare-oriented model later, point `MEDICAL_LLM_MODEL` and `MEDICAL_LLM_BASE_URL` at an OpenAI-compatible provider or your own hosted model.

Examples worth evaluating carefully:

- `aaditya/Llama3-OpenBioLLM-8B`
- `FreedomIntelligence/HuatuoGPT-o1-8B`
- `epfl-llm/meditron-7b`

## Clone and Run

### Prerequisites

- Python 3.11+
- Node.js 20+ and npm
- Expo Go on your phone, or an iOS simulator / Android emulator

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd GenAI-Practitioner-v2
```

### 2. Backend setup

Create a virtual environment, install dependencies, and start the backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
./backend/run_services.sh
```

Gateway:

```bash
curl http://127.0.0.1:8000/health
```

The backend works without any LLM credentials. If you want the optional medical wording layer, copy the example file and add your own key:

```bash
cp backend/.env.example backend/.env
```

### 3. Mobile app setup

```bash
cd mobile-app
npm install
npm start
```

### 4. Real-device setup for Expo Go

If you are testing on a phone, the app needs your computer's LAN IP so the phone can reach the backend.

1. Find your LAN IP on macOS:

```bash
ipconfig getifaddr en0
```

2. Copy the example env file and set the value:

```bash
cp .env.example .env
```

Then edit `.env` so it looks like:

```bash
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.50:8000
```

3. Restart Expo:

```bash
npm start
```

If you are using a simulator on the same machine, the app can usually connect without setting `.env`.

## Optional LLM Configuration

Copy the example file only if you want LLM refinement/chat:

```bash
cp backend/.env.example backend/.env
```

Then add your own token inside `backend/.env`.

Without this file, the app still works in rules + RAG mode.

## Project Structure

```text
backend/
  main.py
  run_services.sh
  services/
mobile-app/
  App.tsx
  package.json
```

## Troubleshooting

- If Expo says the local service is unavailable, make sure the backend is still running and that `mobile-app/.env` contains your current LAN IP.
- If you change networks, your LAN IP may change and you may need to update `mobile-app/.env`.
- If the optional LLM is not configured, the app should still work using deterministic triage plus local retrieval.

## Store Build Notes

This repo includes Expo `app.json` and `eas.json`, so you can produce Android and iOS builds once your backend is deployed over HTTPS.

Typical production flow:

```bash
cd mobile-app
npx eas build -p android --profile production
npx eas build -p ios --profile production
```

Before release:

- deploy the backend to a public HTTPS URL
- set `EXPO_PUBLIC_API_BASE_URL` in the `production` EAS profile
- keep the disclaimer text intact
- avoid diagnosis claims in the store listing

## Safety Position

This is an educational triage prototype for coursework and demonstration. It is not a medical diagnosis system, it should not replace clinicians, and it should always escalate emergency warning signs immediately.
