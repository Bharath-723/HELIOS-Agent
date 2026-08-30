# HELIOS — Google Search Integration Report

## Environment Integration

Google Search configuration is managed through `EnvironmentManager` (`core/system/environment.py`):
- `GOOGLE_API_KEY`: API credential loaded strictly from `.env` environment variables.
- `GOOGLE_SEARCH_ENABLED`: Boolean flag enabling cloud search.
- `GOOGLE_SEARCH_REGION`: Defaulting to `IN` (India).
- `GOOGLE_SEARCH_LANGUAGE`: Defaulting to `en`.

## Secret Protection Policy

1. API keys are NEVER exposed in Tkinter UI cards or LLM prompts.
2. `get_masked_config()` automatically masks `GOOGLE_API_KEY` in system diagnostic logs.
3. Razorpay payment secrets and Google API keys remain completely isolated.
