# Railway Deployment Guide for Kasparro

This project is fully optimized for Railway. Follow these steps to deploy your production-grade backend.

## Step 1: Push Code to GitHub
Ensure all your latest changes from Replit are in GitHub:
1. Open the **Shell** tab in Replit.
2. Run these commands:
   ```bash
   git add .
   git commit -m "Final production-ready implementation"
   git push origin main
   ```

## Step 2: Create a Railway Project
1. Log in to [Railway.app](https://railway.app/).
2. Click **+ New Project**.
3. Select **Deploy from GitHub repo**.
4. Choose your `kasparro-backend-...` repository.
5. Click **Deploy Now**.

## Step 3: Add PostgreSQL Database
Railway requires a database to store your crypto data:
1. In your Railway project dashboard, click **+ New**.
2. Select **Database** -> **Add PostgreSQL**.
3. Railway will automatically create the database.

## Step 4: Configure Environment Variables
You need to tell the app where the database is and provide API keys:
1. Click on your **Service** (the one created from your GitHub repo).
2. Go to the **Variables** tab.
3. Click **+ New Variable** -> **Add Variable from another Service**.
4. Select your **Postgres** service and choose **DATABASE_URL**.
   - *Important*: Ensure the key name is exactly `DATABASE_URL`.
5. Add these additional variables:
   - `COINPAPRIKA_API_KEY`: Set to `none` (the app handles it if empty).
   - `COINGECKO_API_KEY`: Set to `none`.
6. Railway will automatically redeploy with these settings.

## Step 5: Verify Deployment
1. Once the deploy is finished, go to the **Settings** tab of your service.
2. Under **Networking**, click **Generate Domain** to get your public URL.
3. Visit `your-url.up.railway.app/health` to see the status.
4. Visit `your-url.up.railway.app/docs` for the interactive API documentation.

## Technical Notes
- **Port**: The app is configured to listen on port 5000, which Railway detects automatically via the `Dockerfile`.
- **Startup**: The `entrypoint.sh` script automatically runs the ETL pipeline before starting the API.
