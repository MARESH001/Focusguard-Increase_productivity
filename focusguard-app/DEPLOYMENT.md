# 🚀 FocusGuard Deployment Guide

## Backend Deployment (Render)

### 1. Prepare Your Repository
- Push your code to GitHub/GitLab
- Ensure all files are committed

### 2. Deploy to Render
1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Web Service"
3. Connect your repository
4. Configure the service:
   - **Name**: `focusguard-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (or paid for better performance)

### 3. Environment Variables
Add these in Render dashboard:
- `MONGODB_URL`: Your MongoDB connection string
  - Local: `mongodb://localhost:27017`
  - Atlas: `mongodb+srv://username:password@cluster.mongodb.net/focusguard`

### 4. Get Your Backend URL
After deployment, you'll get a URL like: `https://focusguard-backend.onrender.com`

## Frontend Deployment (Netlify)

### 1. Prepare Frontend
1. Update the API URL in your frontend environment
2. Push changes to your repository

### 2. Deploy to Netlify
1. Go to [netlify.com](https://netlify.com) and sign up/login
2. Click "New site from Git"
3. Connect your repository
4. Configure the build:
   - **Base directory**: `home/ubuntu/focusguard-frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `dist`

### 3. Environment Variables
Add these in Netlify dashboard:
- `VITE_API_URL`: Your Render backend URL (e.g., `https://focusguard-backend.onrender.com`)

### 4. Update Backend CORS
Update the CORS origins in `main.py` with your Netlify domain:
```python
allow_origins=[
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
    "https://your-app-name.netlify.app",  # Your actual Netlify domain
    "https://*.netlify.app"
]
```

## 🎯 Quick Deployment Checklist

### Backend (Render)
- [ ] Code pushed to GitHub
- [ ] Render service created
- [ ] Environment variables set (MONGODB_URL)
- [ ] Service deployed successfully
- [ ] Backend URL obtained

### Frontend (Netlify)
- [ ] Code pushed to GitHub
- [ ] Netlify site created
- [ ] Environment variables set (VITE_API_URL)
- [ ] Site deployed successfully
- [ ] CORS updated in backend

## 🔧 Troubleshooting

### Common Issues:
1. **Build fails**: Check if all dependencies are in requirements.txt
2. **CORS errors**: Ensure your Netlify domain is in the CORS origins
3. **WebSocket connection fails**: Check if using wss:// for HTTPS
4. **MongoDB connection fails**: Verify your MONGODB_URL is correct

### Testing:
1. Test backend: Visit your Render URL + `/` (should show "FocusGuard API is running!")
2. Test frontend: Visit your Netlify URL and try logging in

## 📝 Notes
- Free tiers have limitations (cold starts, build minutes)
- Consider upgrading for production use
- Monitor your MongoDB usage if using Atlas 