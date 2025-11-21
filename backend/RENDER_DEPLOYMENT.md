# Render Deployment Guide

This guide explains how to deploy the VelocityInsight backend to Render.

## Prerequisites

- A [Render](https://render.com) account
- Your project pushed to a Git repository (GitHub, GitLab, or Bitbucket)

## Configuration Files

### `start.py`
The startup script that:
- Binds to `0.0.0.0` to accept external connections
- Reads the `PORT` environment variable (provided by Render)
- Defaults to port 8000 for local development
- Configures reload based on the `ENV` variable

### `render.yaml`
The Render configuration file that defines:
- Service type: Python web service
- Build command: `pip install -r requirements.txt`
- Start command: `python start.py`
- Python version: 3.11.0

## Deployment Steps

### Option 1: Using render.yaml (Recommended)

1. **Push your code** to your Git repository including the `render.yaml` file

2. **Create a new Blueprint Instance** in Render:
   - Go to your [Render Dashboard](https://dashboard.render.com/)
   - Click "New" → "Blueprint"
   - Connect your repository
   - Render will automatically detect `render.yaml` and configure your service

3. **Configure environment variables** (if needed):
   - In the Render dashboard, go to your service settings
   - Add any required environment variables from your `.env` file
   - Common variables might include database URLs, API keys, etc.

### Option 2: Manual Setup

1. **Create a new Web Service** in Render:
   - Go to your [Render Dashboard](https://dashboard.render.com/)
   - Click "New" → "Web Service"
   - Connect your repository

2. **Configure the service**:
   - **Name**: `velocityinsight-backend` (or your preferred name)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python start.py`

3. **Add environment variables**:
   - Set `PYTHON_VERSION` to `3.11.0`
   - Set `ENV` to `production`
   - Add any other required variables from your `.env` file

## Local Testing

Test the deployment configuration locally:

```bash
# Set the PORT environment variable
export PORT=8000
export ENV=production

# Run the start script
python start.py
```

The server should start on `http://0.0.0.0:8000`

## Accessing Your Deployed API

Once deployed, Render will provide you with a URL like:
```
https://velocityinsight-backend.onrender.com
```

Your API endpoints will be available at:
- Root: `https://velocityinsight-backend.onrender.com/`
- Docs: `https://velocityinsight-backend.onrender.com/docs`
- Any other endpoints defined in your routers

## Updating CORS Settings

If your frontend is hosted on a different domain, update the CORS settings in `app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend-domain.com",
        "http://localhost:5173",  # For local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Troubleshooting

### Service won't start
- Check the Render logs for error messages
- Verify all dependencies are listed in `requirements.txt`
- Ensure your Python version matches the one specified

### Connection refused
- Make sure the app is binding to `0.0.0.0`, not `localhost` or `127.0.0.1`
- Verify the `PORT` environment variable is being read correctly

### Missing environment variables
- Double-check all variables from your `.env` file are added in Render's dashboard
- Remember that `.env` files are not deployed to production for security reasons

## Free Tier Limitations

Render's free tier has some limitations:
- Services spin down after 15 minutes of inactivity
- First request after spin-down may take 30-60 seconds
- Consider upgrading to a paid plan for production use

## Next Steps

After deployment:
1. Update your frontend's API URL to point to your Render deployment
2. Test all endpoints to ensure they work correctly
3. Set up any required database connections
4. Configure monitoring and logging as needed
