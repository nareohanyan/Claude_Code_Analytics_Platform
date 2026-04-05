# LLM Usage Log

## AI Tools Used

- ChatGPT
- Codex
- Gemini

## Candidate Ownership

Project direction and architecture were defined manually by me.

- Selected stack: PostgreSQL + Docker, SQLAlchemy, Alembic, FastAPI, Streamlit.
- Defined structure: reusable package layout, ETL layer, analytics layer, API layer, dashboard layer.
- Chose optional enhancements: API access and predictive analytics.
- Controlled implementation sequence, reviewed outputs, and approved each change step-by-step.

## How LLMs Assisted

LLMs were used to accelerate implementation, not to replace decision-making.

- Generate draft implementations for modules and endpoints.
- Refactor repetitive boilerplate.
- Suggest code-level improvements and documentation wording.
- Speed up iteration during bug fixing and UI adjustments.

## Representative Prompt Themes

- "Use PostgreSQL through Docker with Alembic migrations."
- "Keep the codebase structured and reusable."
- "Implement API bonus and connect dashboard to API."
- "Add predictive analytics and expose it in API/UI."
- "Prepare submission-quality README and deliverables."

## Validation Performed Manually

All generated output was verified before being accepted:

- database migration checks (`alembic upgrade head`)
- ETL load verification (data presence and row counts)
- API verification via Swagger and `curl`
- dashboard behavior checks (navigation, data loading, dark mode readability)
- code sanity checks (`python -m compileall`)

## Summary

AI tools were used as engineering assistants for speed.
Architecture, technical decisions, quality control, and final acceptance remained candidate-driven.
