# Testing Instructions

This project uses integration scripts for backend testing and standard linting/manual verification for the frontend.

## Backend Testing

The backend tests are integration tests that require the FastAPI server to be running.

### 1. Start the Backend Server

Open a terminal and run:

```bash
# From the project root
cd backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Ensure the server is running at `http://127.0.0.1:8000`.

### 2. Run Test Scripts

Open a **new terminal window** (keep the server running) and execute the test scripts.

#### Basic Connectivity Test
Runs a quick check of the main endpoints.

```bash
# From the project root
python3 backend/test_backend.py
```

#### Comprehensive Endpoint Test
Tests all 20+ API endpoints including ML predictions and strategy simulations.

```bash
# From the project root
python3 backend/test_all_endpoints.py
```

## Frontend Testing

### 1. Linting
Run the linter to catch static analysis errors.

```bash
# From the project root
cd frontend
npm run lint
```

### 2. Manual Verification
Since there are no automated UI tests, verify the following flows manually in the browser:

1.  **Driver Training**:
    - Select a Track, Race, and Vehicle.
    - Click "Analyze Performance".
    - Verify charts and AI insights load.
2.  **Pre-Event Prediction**:
    - Navigate to "Pre-Event Prediction".
    - Select a track and run predictions.
3.  **Post-Event Analysis**:
    - Navigate to "Post-Event Analysis".
    - Verify race summary and strategy analysis.
