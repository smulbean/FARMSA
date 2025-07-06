# FARMSA - Dispersion Options Strategy Backtester

This project contains a backend API built with FastAPI and a React frontend for running and visualizing dispersion options strategy backtesting using Polygon.io data.

---

## Prerequisites

- Python 3.9+ (for backend)
- Node.js 16+ and npm/yarn (for frontend)
- Polygon.io API Key (required for backend data fetching)

---

## Backend Setup

### 1. Navigate to the backend directory

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

pip install -r requirements.txt
source venv/bin/activate
```

Don't forget to add an backend/.env file for your API key

```bash
POLYGON_API_KEY=your_polygon_api_key_here
```
To run the server: 
```bash
uvicorn main:app --reload --port 8000
```
The API will be available at ```http://127.0.0.1:8000 ```

### 1. Navigate to the frontend directory

```bash
cd frontend
npm install
```

To run the frontend: 
```bash
npm start
```
