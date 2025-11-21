# Render Deployment Checklist

## ✅ Pre-Deployment (Completed)

- [x] Created `start.py` with proper port binding (0.0.0.0)
- [x] Created `render.yaml` with service configuration
- [x] Fixed `app/core/config.py` to handle missing environment variables
- [x] Added default values for all config settings
- [x] Made `GEMINI_API_KEY` optional
- [x] Created `.renderignore` to exclude unnecessary files
- [x] Verified config loads without errors locally

## 📋 Deployment Steps

### 1. Push Changes to Git
```bash
cd /Users/arsh/Developer/Projects/VelocityInsight
git add backend/
git commit -m "Configure backend for Render deployment with environment variable fixes"
git push origin main
```

### 2. Deploy to Render

**Option A: Using Blueprint (Recommended)**
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **Blueprint**
3. Connect your GitHub/GitLab repository
4. Render will auto-detect `backend/render.yaml`
5. Click **Apply** to create the service

**Option B: Manual Setup**
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **Web Service**
3. Connect your repository
4. Configure:
   - **Name**: `velocityinsight-backend`
   - **Root Directory**: `backend`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python start.py`

### 3. Configure Environment Variables (Optional)

Go to your service → **Environment** tab → Add variables:

**Required for AI Features:**
- `GEMINI_API_KEY` = `your-api-key-here`

**Optional (already have defaults):**
- `DATASET_ROOT` = `./data` (default)
- `DEFAULT_TRACK` = `barber` (default)
- `DEFAULT_RACE` = `R1` (default)

### 4. Wait for Deployment

- Monitor the deploy logs in Render
- First deploy may take 5-10 minutes
- Look for: `INFO: Uvicorn running on http://0.0.0.0:XXXX`

### 5. Test Your Deployment

Once deployed, test the endpoints:

```bash
# Replace with your Render URL
export API_URL="https://velocityinsight-backend.onrender.com"

# Test root endpoint
curl $API_URL/

# Test API docs (open in browser)
echo "$API_URL/docs"
```

Expected response from root:
```json
{
  "status": "ok",
  "service": "gr-insight",
  "version": "1.0.0",
  "description": "Real-time race strategy & analytics for Toyota GR Cup"
}
```

### 6. Update Frontend

Update your frontend's API URL to point to Render:

**In `/Users/arsh/Developer/Projects/VelocityInsight/frontend/.env`:**
```env
VITE_API_URL=https://velocityinsight-backend.onrender.com
```

## 🔧 Troubleshooting

### Build Fails
- Check that all dependencies in `requirements.txt` are compatible with Python 3.13
- Review build logs in Render dashboard

### Service Won't Start
- Verify environment variables are set correctly
- Check application logs for specific errors
- Ensure `rootDir: backend` is set in `render.yaml`

### "No open ports detected" Error
- This should now be fixed with the config changes
- Verify `start.py` is using `0.0.0.0` as host
- Check that PORT environment variable is being read

### CORS Issues
- Update `backend/app/main.py` allowed origins to include your frontend domain
- Currently set to `allow_origins=["*"]` (allow all)

## 📊 Monitoring

After deployment:
- Monitor service health in Render dashboard
- Check application logs for errors
- Set up alerts for downtime (Render Pro feature)
- Monitor API response times

## 💰 Cost Considerations

**Free Tier:**
- Services spin down after 15 minutes of inactivity
- 750 hours/month free
- First request after spin-down takes ~30-60 seconds (cold start)

**Paid Plans ($7+/month):**
- No spin-down
- Faster performance
- Custom domains
- Auto-scaling

## ✨ Next Steps After Successful Deployment

1. ✅ Deploy frontend to Render/Vercel/Netlify
2. ✅ Update frontend API URL to point to backend
3. ✅ Test all endpoints with real data
4. ✅ Set up custom domain (optional)
5. ✅ Configure database if needed
6. ✅ Set up monitoring and alerts
