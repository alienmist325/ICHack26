# Property Rental Finder - Database Setup

## Installation

1. Make sure you have `uv` installed
2. Install dependencies:
```bash
cd backend
uv add fastapi uvicorn pydantic
```
3. Initialise the database:
```bash
cd backend
uv run -m app.database
```
4. Run the API server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```