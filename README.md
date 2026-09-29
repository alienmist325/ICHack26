# LeftMove

**Stuck in estate agent hell? The right move is LeftMove.**

LeftMove is an IC Hack 2026 rental search project. It brings Rightmove listings into a searchable feed, helps people find homes that fit practical needs such as budget and commute, and uses community feedback to identify listings that may no longer be available. An optional AI calling workflow can ask estate agents whether a saved property is still on the market.

## Features

- Search and filter listings by text, price, bedrooms, property type, furnishing, and postcode area.
- Find homes within a travel-time radius and compare travel times to key locations.
- Optionally check availability through Bland AI calls to estate agents.

## Technologies

The frontend uses React, TypeScript with Vite. The Python backend uses FastAPI, Pydantic, and SQLite. 

Listings come from Apify's `dhrumil/rightmove-scraper` actor. Routing uses `routingpy`, GraphHopper (or Mapbox), and Shapely; the optional calling workflow uses Bland AI.

## Run locally

Install Python 3.12 or newer, [uv](https://docs.astral.sh/uv/), Node.js, and pnpm. Run backend commands from the repository root.

### 1. Clone and install dependencies

```bash
git clone https://github.com/alienmist325/ICHack26.git
cd ICHack26
uv sync
```

### 2. Configure the backend

```bash
cp .env.example .env
```

Edit `.env` for the integrations you want:

| Variable | Needed for |
| --- | --- |
| `APIFY_API_KEY` | Importing listings through the scraper CLI |
| `ROUTING_API_KEY` | Commute and distance features with GraphHopper (the default provider) |
| `ROUTING_PROVIDER` | Optional; defaults to `graphhopper`, with `mapbox` also supported |
| `BLAND_AI_API_KEY` | Real automated availability calls |
| `BLAND_AI_MOCK_MODE`, `BLAND_AI_MOCK_PHONE_NUMBER` | Testing calls against a number you control |

The sample file includes other optional settings. The API can start without external API keys, but the corresponding features need them. Authentication reads `SECRET_KEY` directly from the process environment, so set it in your shell before launching the backend:

```bash
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

### 3. Start the backend

From the repository root:

```bash
uv run uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend initialises its SQLite tables at startup in `backend/data/rightmove.db`. Check [http://localhost:8000/health](http://localhost:8000/health) and browse the API at [http://localhost:8000/docs](http://localhost:8000/docs).

### 4. Start the frontend

In a second terminal:

```bash
cd frontend
pnpm install
pnpm dev
```

The frontend will open at [http://localhost:5173](http://localhost:5173)). 

### 5. Import listings (optional)

An empty database will show no listings until you import some.

After setting `APIFY_API_KEY` in the root `.env`, run this from the repository root, using a real Rightmove results URL:

```bash
uv run rightmove-scraper --list-url "https://www.rightmove.co.uk/..." --max-properties 20
```

For one listing, use `--property-url "https://www.rightmove.co.uk/properties/..."`.

**Note the external scraper may incur usage charges.**

## Project layout

```text
backend/
  app/                 API, routers, schemas, SQLite access
  services/            Scraper, routing, geocoding, verification
  cli/                 Listing import command
  tests/               Backend tests
frontend/
  src/                 React pages, components, hooks, API client
```

## Development

From the repository root, run `uv run pytest backend/tests`. For frontend checks, run `pnpm build` and `pnpm lint` inside `frontend/`. 

Additional API documentation is in [SCRAPER_API.md](SCRAPER_API.md), [ROUTING_SERVICE.md](ROUTING_SERVICE.md), and [GEOCODING_ENDPOINT.md](GEOCODING_ENDPOINT.md).
