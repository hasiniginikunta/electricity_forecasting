# Electricity Forecasting – integration handoff

This version contains initial frontend/backend integration fixes. It is not a claim that every screen is fully backed by live data yet.

## What was changed

- Vite now runs on port 5173 (Spring Boot remains on 8080).
- Added a Vite `/api` proxy for local development and Docker Compose networking.
- Replaced the frontend API client's silent mock-data fallback with real HTTP requests and visible errors.
- Registration now registers and then logs in, because the backend registration endpoint returns a user rather than a JWT.
- Forecast API typing now reflects the backend's list response; the forecast page displays the first returned record.
- Consumption and bill DTO fields are mapped from backend names (`billingMonth`, `kwhConsumed`, `billAmount`) to the existing UI model.
- Updated the frontend Dockerfile to use the repository's existing pnpm lockfile instead of requiring a missing npm lockfile.

## Run locally with Docker

1. Install and start Docker Desktop.
2. Copy `.env.example` to `.env` in this project root.
3. From this directory run: `docker compose up --build`.
4. Open the frontend at http://localhost:5173. Spring Boot is at http://localhost:8080.

## Important remaining work

- Several screens still intentionally use sample data (notably dashboard, recommendations, challenges, and parts of consumption/forecast visualizations). They need real backend data wiring and any missing endpoints.
- Replace hard-coded household ID `1` in page components with the authenticated user's actual household ID.
- Verify backend database configuration and seed required forecast/benchmark/household data.
- Confirm JWT authorization rules and DTO validation against real registration/login requests.
- The frontend may need dependency installation/build verification in your environment; this handoff was not executed against your local Docker/database.

## API behavior

Frontend requests use relative `/api/...` URLs. Vite proxies these to Spring Boot. API errors now reject instead of returning mock data, so a failed request is visible to the UI/caller.
