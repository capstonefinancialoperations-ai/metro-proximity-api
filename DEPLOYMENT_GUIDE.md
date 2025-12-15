# Deployment Guide: Metro Proximity API to Render

## ✅ What We've Done So Far

1. ✅ Created Flask app (`app.py`)
2. ✅ Created requirements file (`requirements.txt`)
3. ✅ Downloaded Census CBSA shapefile data
4. ✅ Set up project structure

## 📋 Next Steps

### Step 1: Install Git (if not already installed)

**Download Git for Windows:**
1. Go to: https://git-scm.com/download/win
2. Download and install Git
3. During installation, use default settings
4. Restart PowerShell after installation

### Step 2: Test App Locally (Optional but Recommended)

Open PowerShell in the project directory and run:

```powershell
cd C:\Users\danielle\metro-proximity-api

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

The app should start on http://localhost:5000

**Test it:**
Open a new PowerShell window and run:
```powershell
curl "http://localhost:5000/check-proximity?lat=40.7128&lon=-74.0060"
```

You should see JSON response with NYC metro area info!

Press `Ctrl+C` to stop the server when done testing.

### Step 3: Create GitHub Repository

1. **Create GitHub account** (if you don't have one):
   - Go to https://github.com/signup

2. **Create new repository:**
   - Go to https://github.com/new
   - Repository name: `metro-proximity-api`
   - Set to **Public** (required for Render free tier)
   - Do NOT initialize with README (we already have files)
   - Click "Create repository"

### Step 4: Push Code to GitHub

In PowerShell, in your project directory:

```powershell
cd C:\Users\danielle\metro-proximity-api

# Initialize git repository
git init

# Add all files
git add .

# Commit files
git commit -m "Initial commit: Metro proximity API"

# Add GitHub remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/metro-proximity-api.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Note:** You may be prompted to log in to GitHub. Use your GitHub credentials.

### Step 5: Create Render Account and Deploy

1. **Sign up for Render:**
   - Go to https://render.com/
   - Click "Get Started for Free"
   - Sign up with GitHub (recommended - easier integration)

2. **Create New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub account if prompted
   - Select your `metro-proximity-api` repository
   - Click "Connect"

3. **Configure the service:**
   - **Name:** `metro-proximity-api` (or your preferred name)
   - **Region:** Choose closest to you
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** `Free`

4. **Click "Create Web Service"**

Render will now:
- Clone your repository
- Install dependencies
- Start your app
- Give you a URL like: `https://metro-proximity-api.onrender.com`

**⏱️ First deployment takes 5-10 minutes** (downloading Census data, installing libraries, etc.)

### Step 6: Test Your Deployed API

Once deployment is complete (status shows "Live"), test it:

```
https://your-app-name.onrender.com/check-proximity?lat=40.7128&lon=-74.0060&max_distance=50
```

Replace `your-app-name` with your actual Render app name.

You should see JSON response with metro area information!

## 🔗 Using with Make.com

Once deployed, use your Render URL in Make:

1. **In Make scenario:**
   - Add "HTTP" module (Make a request)
   - Method: GET
   - URL: `https://your-app.onrender.com/check-proximity`
   - Query String:
     - `lat`: (from geocoding step)
     - `lon`: (from geocoding step)
     - `max_distance`: 50

2. **Parse the response:**
   - Check `within_range` field (true/false)
   - Get `nearest_metro.name` if needed
   - Get `nearest_metro.distance_to_edge_miles`

3. **Update Monday board:**
   - Use the response to update status column
   - Example: "Within 50 miles of NYC Metro" or "Not near metro area"

## 📝 Important Notes

### Free Tier Limitations:
- **Render free tier:** App may "spin down" after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds to wake up
- 750 hours/month free (sufficient for this use case)

### Keeping App Awake (Optional):
If you want instant responses, you can:
1. Upgrade to paid tier ($7/month for always-on)
2. Use a service like UptimeRobot to ping your app every 10 minutes

## 🆘 Troubleshooting

### "Metro data not loaded" error:
- The `data/` folder with shapefiles must be in your GitHub repo
- Check that shapefile uploaded correctly (files are large)

### Deployment fails:
- Check Render logs for specific error
- Ensure `requirements.txt` is correct
- Verify Python version compatibility

### Git push fails:
- Make sure you replaced YOUR_USERNAME with actual GitHub username
- Check GitHub authentication (may need personal access token)

## 🎉 You're Done!

Your metro proximity API is now running 24/7 in the cloud and ready to use with Make and Monday.com!
