# Kasparro Backend & ETL

## 1. Project Overview
The **Kasparro Backend & ETL** is a production-grade system designed for ingesting, normalizing, and serving cryptocurrency asset data. It solves the problem of data fragmentation by aggregating information from multiple sources (CoinGecko, CoinPaprika, and CSV files) into a unified PostgreSQL schema. The system ensures high data integrity and provides a clean API for downstream applications.

## 2. Tech Stack
- **Python**: The core programming language used for its rich ecosystem in data processing.
- **FastAPI**: A modern, high-performance web framework for building APIs with asynchronous support.
- **SQLAlchemy**: An industry-standard ORM used for robust database interactions and schema management.
- **PostgreSQL**: A powerful relational database for reliable and scalable data storage.
- **Railway**: The cloud platform used for seamless deployment and infrastructure management.
- **ETL Concepts**: Implements Extract, Transform, and Load patterns to maintain a clean, canonical data state.

## 3. System Architecture (Step-by-Step)
1. **API Layer (FastAPI)**: Serves as the entry point, providing validated endpoints for data retrieval and system status.
2. **ETL Pipeline Flow**: Orchestrates the extraction of raw data, transformation into a unified format, and loading into the canonical database tables.
3. **Database Layer**: Uses a dual-stage storage strategy with raw ingestion tables and clean, normalized identity tables.
4. **Service Layer Separation**: Business logic is decoupled from the API routes into specialized services (`APIService`, `ETLService`).
5. **Background Task Execution**: Long-running ETL processes are handled asynchronously via FastAPI's `BackgroundTasks`.

## 4. API Endpoints

### GET /
- **Purpose**: Service discovery and status.
- **Method**: `GET`
- **Sample Response**:
  ```json
  {
    "service": "Kasparro Backend & ETL",
    "status": "ok",
    "endpoints": { "docs": "/docs", "health": "/health", ... }
  }
  ```

### GET /docs
- **Purpose**: Interactive Swagger API documentation.
- **Method**: `GET`
- **Sample Response**: (HTML Documentation Page)

### GET /health
- **Purpose**: System health check and database status.
- **Method**: `GET`
- **Sample Response**:
  ```json
  { "status": "ok", "db": true, "last_etl": "2026-01-01T12:00:00Z" }
  ```

### GET /data
- **Purpose**: Retrieve unified coin assets with pagination and search.
- **Method**: `GET`
- **Sample Response**:
  ```json
  {
    "total": 1200,
    "data": [{ "id": 1, "symbol": "BTC", "name": "Bitcoin", ... }]
  }
  ```

### GET /stats
- **Purpose**: Summary of ETL run performance and record counts.
- **Method**: `GET`
- **Sample Response**:
  ```json
  { "total_runs": 15, "total_records_processed": 50000 }
  ```

### POST /etl/run
- **Purpose**: Manually trigger the full ETL pipeline.
- **Method**: `POST`
- **Sample Response**:
  ```json
  { "status": "accepted", "message": "ETL run started in background" }
  ```

## 5. Folder Structure
```text
kasparro-backend/
│
├── api/                # FastAPI route definitions (main.py)
├── core/               # Shared logic: DB, Models, Logging, Config
├── services/           # Business logic: API and ETL orchestration
├── ingestion/          # ETL source adapters and processing logic
├── README.md           # Project documentation
├── requirements.txt    # Python dependencies
└── Dockerfile          # Container configuration
```

## 6. Local Setup (Step-by-Step)
1. **Clone Repository**:
   ```bash
   git clone <repository-url>
   cd kasparro-backend
   ```
2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Set Environment Variables**:
   Create a `.env` file with:
   - `DATABASE_URL=postgresql://user:pass@localhost:5432/db`
   - `COINPAPRIKA_API_KEY=your_key_here`
5. **Run the Server**:
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 5000 --reload
   ```

## 7. Deployment (Railway)
The application is optimized for Railway deployment. It utilizes the `PORT` environment variable provided by the platform and includes a production-ready `uvicorn` configuration. Deployment is automated via GitHub integration.

## 8. ETL Flow Explanation
- **Trigger**: The ETL is triggered via a `POST /etl/run` request or scheduled tasks.
- **Fetch**: Data is extracted from external APIs (CoinGecko, CoinPaprika) or local CSV files.
- **Store**: Records are first staged in `raw_assets`, then transformed and upserted into the canonical `coins` and `coin_sources` tables.
- **Read**: The `/data` endpoint performs optimized joins across these tables to present a unified view of the assets.
