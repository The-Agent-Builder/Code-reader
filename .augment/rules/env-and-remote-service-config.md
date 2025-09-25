Title: Frontend env fallback and external service base URLs

Context:
- We integrate an external README/DeepWiki service.
- In Vite, only variables prefixed with VITE_ are exposed to the client bundle.

Rules:
1) Always expose backend .env values to the frontend by mapping to Vite vars in vite.config.ts define:
   - Map README_API_BASE_URL -> VITE_README_API_BASE_URL if the latter is not set.
   - Map API_BASE_URL -> VITE_API_BASE_URL if the latter is not set.
   - Map DEEPWIKI_UPLOAD_FILEPATH -> VITE_DEEPWIKI_UPLOAD_FILEPATH if the latter is not set.

2) In frontend code, never default external service URLs to relative paths that resolve to the dev server (e.g., '/deepwiki'). Always require explicit base URLs via env (VITE_*) and fail fast with a clear error when missing.

3) Keep step definitions and switch-case execution in sync. If the UI lists steps [scan, knowledge base, analyze data model, generate docs], the switch must implement cases 0..3 accordingly.

Why:
- Prevents accidental calls to http://localhost:3000 due to relative paths.
- Makes local/dev/docker deployments consistent and configurable via .env.
- Avoids 404/flow issues caused by mismatched step order.

Applies to:
- All future integrations with external services in the frontend.
- Any feature with multi-step flows shown in the UI.

