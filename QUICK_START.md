# Quick Start Guide

## ✅ What's Ready

Your Metro Proximity API is **ready to deploy**! Here's what we've built:

### Files Created:
- ✅ `app.py` - Flask API that checks metro proximity using Census data
- ✅ `requirements.txt` - Python dependencies (tested and working)
- ✅ `data/` - Contains Census CBSA shapefile (935 metro areas loaded)
- ✅ `.gitignore` - Excludes unnecessary files from Git
- ✅ `README.md` - Full API documentation
- ✅ `DEPLOYMENT_GUIDE.md` - Step-by-step deployment instructions

### API Tested Locally ✓
Successfully tested with NYC coordinates:
```json
{
  "within_range": true,
  "is_inside_metro": true,
  "nearest_metro": {
    "name": "New York-Newark-Jersey City, NY-NJ",
    "cbsa_code": "35620",
    "distance_to_edge_miles": 0
  }
}
```

## 🚀 Next Steps to Deploy

### 1. Install Git (if needed)
Download from: https://git-scm.com/download/win

### 2. Create GitHub Account
Sign up at: https://github.com/signup

### 3. Push Code to GitHub

In PowerShell (in the project directory):
```powershell
cd C:\Users\danielle\metro-proximity-api

# Initialize repository
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Metro proximity API"

# Add your GitHub repo (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/metro-proximity-api.git

# Push
git branch -M main
git push -u origin main
```

### 4. Deploy to Render

1. Go to https://render.com/
2. Sign up (use GitHub for easier integration)
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free
6. Click "Create Web Service"

**Wait 5-10 minutes for first deployment**

### 5. Get Your API URL

Once deployed, Render gives you a URL like:
```
https://metro-proximity-api-xxxx.onrender.com
```

Test it:
```
https://your-app.onrender.com/check-proximity?lat=40.7128&lon=-74.0060
```

## 🔧 Using with Make.com

### Basic Make Scenario:

1. **Trigger:** Monday.com - Watch Column Values (address column)

2. **Module 1:** Google Maps - Geocode Address
   - Input: Address from Monday
   - Output: Latitude, Longitude

3. **Module 2:** HTTP - Make a Request
   - Method: GET
   - URL: `https://your-app.onrender.com/check-proximity`
   - Query String:
     - `lat`: {{latitude from geocoding}}
     - `lon`: {{longitude from geocoding}}
     - `max_distance`: 50

4. **Module 3:** Monday.com - Update Item
   - Map fields:
     - `within_range` → Status column
     - `nearest_metro.name` → Text column
     - `nearest_metro.distance_to_edge_miles` → Number column

### Example Make Logic:

**If `within_range` = true:**
- Update Monday status to "✓ Near Metro"
- Set text field to metro name

**If `within_range` = false:**
- Update Monday status to "✗ Not Near Metro"
- Leave metro name blank

## 📊 API Response Fields

### Success Response:
```json
{
  "within_range": true/false,
  "is_inside_metro": true/false,
  "nearest_metro": {
    "name": "Metro Area Name",
    "cbsa_code": "12345",
    "distance_to_edge_miles": 0 or number
  },
  "all_nearby_metros": [...]
}
```

### Key Fields for Make:
- **`within_range`**: Is location within 50 miles? (boolean)
- **`is_inside_metro`**: Is location inside a metro area? (boolean)
- **`nearest_metro.name`**: Name of nearest metro
- **`nearest_metro.distance_to_edge_miles`**: Miles to metro boundary (0 if inside)

## 💡 Tips

### Render Free Tier:
- App "sleeps" after 15 min of inactivity
- First request after sleep takes ~30 seconds
- Sufficient for Monday board automation

### Custom Distance:
Change the 50-mile default by adding `max_distance` parameter:
```
?lat=40.7128&lon=-74.0060&max_distance=100
```

### Multiple Metros:
The API returns ALL metros within range in `all_nearby_metros` array.

## 📞 Need Help?

- **Deployment issues:** Check `DEPLOYMENT_GUIDE.md`
- **API usage:** Check `README.md`
- **Make integration:** The HTTP module in Make works with any REST API

## 🎉 You're All Set!

Your API is tested and ready. Just need to:
1. Install Git
2. Push to GitHub
3. Deploy to Render
4. Connect to Make

Total time: ~30 minutes
