# GenAI Practitioner v2

GenAI Practitioner v2 is a clean rebuild of the Bournemouth health-triage prototype as a simpler, safer, store-ready mobile system.

## Things Reconsidered in Version 2

The original project already is strong:

- a Python microservices backend
- Bournemouth-specific facility recommendations
- transport suggestions
- an LLM orchestration flow
- two separate mobile clients (`Flutter` and `Expo`)

The main issues were architectural duplication and inconsistent ownership of triage decisions. Version 2 keeps the same product idea but makes the clinical reasoning path explicit:

- one mobile app instead of two
- medical LLM-led clinical triage
- deterministic guardrails that only restrict unsafe or under-escalated answers
- RAG-backed Bournemouth knowledge retrieval before and after the LLM response
- conservative safety fallback only when the LLM is unavailable

That means the app uses the LLM for triage, while the non-LLM code acts as a safety boundary rather than the clinical decision-maker.

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
2. Safety guardrails inspect only for red flags and minimum escalation constraints.
3. The service retrieves Bournemouth and NHS-style guidance through a lightweight RAG layer.
4. A healthcare-oriented LLM chooses the urgency, reasoning, next actions, self-care advice, and search query.
5. Guardrails post-check the LLM output so it cannot under-escalate red flags or offer unsafe self-care for high urgency.
6. Facility and transport services return practical local recommendations based on the final guarded urgency.

## Stack Choices

- Backend: Python + FastAPI
- Mobile: Expo + React Native + TypeScript
- Store packaging: EAS config included for Android/iOS builds
- RAG: lightweight local retrieval over curated Bournemouth knowledge cards
- LLM support: OpenAI-compatible endpoint for healthcare-tuned models

## Recommended Medical Models

The default recommended model is:

- `m42-health/Llama3-Med42-8B:fastest`

It was selected because it is a healthcare-focused Llama 3 8B conversational model available through an OpenAI-compatible Hugging Face Router workflow, which fits a responsive coursework prototype. This is still not a clinically validated deployment choice; it is a prototype model choice that must be guarded, evaluated, and replaced or validated before any real-world use.

The backend remains configurable, so `MEDICAL_LLM_MODEL` and `MEDICAL_LLM_BASE_URL` can point at another OpenAI-compatible provider or a self-hosted model.

## Clone and Run

### Prerequisites

- Python 3.11+
- Node.js 20+ and npm
- Expo Go on your phone, or an iOS simulator / Android emulator

### 1. Clone the repository

```bash
git clone https://github.com/alisan2022/genAI_Practicioner_v2.git
cd genAI_Practicioner_v2
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

Full clinical triage requires an LLM API key. Without credentials, the backend still starts, but triage responses use conservative safety fallback guidance rather than the full LLM-led pathway.

```bash
cp backend/.env.example backend/.env
```

Then edit `backend/.env` and add your own Hugging Face or OpenAI-compatible API key.

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

## LLM Configuration

Copy the example file:

```bash
cp backend/.env.example backend/.env
```

Then add your own token inside `backend/.env`.

Without this file, the app still runs but uses `safety-guardrails` fallback mode for triage.

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
- If the LLM is not configured, the backend should still answer, but the model label will be `safety-guardrails` and the response is conservative fallback guidance.

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

This is an educational triage prototype for coursework and demonstration. It is not a medical diagnosis system, it should not replace clinicians, and it should always use guardrails to escalate emergency warning signs immediately.
