# Railway Deployment Setup Guide

## Current Issues & Solutions

### Issue: Database Connection Failing

**Symptoms:**
- `/health` returns `"db": false`
- `/data` and `/stats` return 500 errors
- ETL hasn't run (`last_etl.status: null`)

**Root Cause:**
Railway deployment doesn't have a PostgreSQL database provisioned or DATABASE_URL is not configured.

## Solution Steps

### Step 1: Provision PostgreSQL Database on Railway

1. Go to your Railway project dashboard
2. Click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
3. Railway will automatically provision a PostgreSQL database
4. Railway will automatically set the `DATABASE_URL` environment variable

### Step 2: Verify Environment Variables

In Railway project settings, ensure these environment variables are set:

- `DATABASE_URL` - Automatically set by Railway when you add PostgreSQL
- `COINPAPRIKA_API_KEY` - Your API key (if you have one)
- `PORT` - Railway sets this automatically (usually 8000 or dynamic)

### Step 3: Redeploy

After adding the database:
1. Railway will automatically redeploy
2. Or manually trigger a redeploy from the dashboard

### Step 4: Verify Connection

Once redeployed, check:
- `/health` should show `"db": true`
- `/data` should return data (may be empty if ETL hasn't run)
- `/stats` should return stats (may show 0 runs if ETL hasn't run)

## Expected Behavior After Fix

### `/health` Response:
```json
{
  "status": "ok",
  "db": true,
  "last_etl": {
    "status": "success",
    "run_started_at": "2025-12-29T..."
  }
}
```

### `/data` Response:
```json
{
  "request_id": "...",
  "api_latency_ms": 123,
  "limit": 50,
  "offset": 0,
  "total": 0,
  "data": []
}
```
(Empty initially until ETL runs)

### `/stats` Response:
```json
{
  "total_runs": 0,
  "total_records_processed": 0,
  "last_success": {
    "timestamp": null,
    "records_processed": null,
    "duration_seconds": null
  },
  "last_failure": {
    "timestamp": null,
    "error": null
  }
}
```

## Troubleshooting

### If DATABASE_URL is not set:
1. Check Railway project settings → Variables
2. Ensure PostgreSQL service is added
3. The `DATABASE_URL` should look like: `postgresql://user:password@host:port/dbname`

### If connection still fails:
1. Check Railway logs for database connection errors
2. Verify PostgreSQL service is running (green status)
3. Check if SSL is required (code handles this automatically)

### Manual DATABASE_URL Format:
If you need to set it manually:
```
postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DATABASE
```

## Code Changes Made

1. **Error Handling**: `/data` and `/stats` now return proper error responses instead of 500
2. **Database URL Normalization**: Handles `postgres://` → `postgresql+psycopg2://` conversion
3. **SSL Support**: Automatically tries SSL with fallback
4. **Better Logging**: More detailed error messages in logs

## Next Steps

1. ✅ Add PostgreSQL database to Railway project
2. ✅ Verify DATABASE_URL is set automatically
3. ✅ Wait for redeploy
4. ✅ Test `/health`, `/data`, `/stats` endpoints
5. ✅ ETL will run automatically in background on next deploy

