# 🚀 FocusGuard Deployment Guide

This guide will help you deploy FocusGuard to Render (Backend) and Netlify (Frontend).

## 📋 Prerequisites

- GitHub repository with your FocusGuard code
- MongoDB Atlas account (for database)
- Render account (for backend)
- Netlify account (for frontend)

## 🔧 Backend Deployment (Render)

### 1. MongoDB Setup
1. Create a MongoDB Atlas cluster
2. Get your connection string
3. Add your IP to the whitelist

### 2. Render Backend Setup
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:

**Basic Settings:**
- **Name**: `focusguard-backend`
- **Environment**: `Python 3`
- **Region**: `Oregon` (or closest to you)
- **Branch**: `main`
- **Root Directory**: `Focusguard-Increase_productivity/focusguard-app`

**Build Command:**
```bash
# Install system dependencies for BERT and ML libraries
apt-get update && apt-get install -y \
  build-essential \
  gcc \
  g++ \
  python3-dev \
  git \
  curl \
  wget

# Upgrade pip and build tools
pip install --upgrade pip setuptools wheel

# Set environment variables for optimized builds
export BLIS_ARCH="x86_64"
export NPY_NUM_BUILD_JOBS=1
export TORCH_CUDA_ARCH_LIST="3.5;5.0;6.0;7.0;7.5;8.0;8.6"
export CUDA_HOME="/usr/local/cuda"

# Install PyTorch CPU version (more compatible with Render)
pip install torch==2.1.0+cpu torchvision==0.16.0+cpu torchaudio==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu

# Install other requirements
pip install --no-cache-dir --prefer-binary -r requirements.txt
```

**Start Command:**
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
```

**Environment Variables:**
- `MONGODB_URL`: Your MongoDB Atlas connection string
- `PYTHON_VERSION`: `3.11.9`
- `PORT`: `8000`
- `TRANSFORMERS_CACHE`: `/tmp/transformers_cache`
- `HF_HOME`: `/tmp/huggingface`
- `TORCH_HOME`: `/tmp/torch`
- `BERT_DISABLE_GPU`: `true`
- `PYTHONPATH`: `/opt/render/project/src`

### 3. Backend Features
✅ **BERT AI Classification** - CPU-optimized for deployment
✅ **Real-time WebSocket notifications**
✅ **MongoDB integration**
✅ **Task and reminder management**
✅ **Custom audio uploads**
✅ **Activity monitoring**

## 🎨 Frontend Deployment (Netlify)

### 1. Netlify Setup
1. Go to [Netlify Dashboard](https://app.netlify.com)
2. Click "New site from Git"
3. Connect your GitHub repository
4. Configure the build:

**Build Settings:**
- **Base directory**: `Focusguard-Increase_productivity/focusguard-frontend`
- **Build command**: `npm run build`
- **Publish directory**: `dist`

**Environment Variables:**
- `VITE_API_URL`: Your Render backend URL (e.g., `https://focusguard-backend.onrender.com`)

### 2. Frontend Features
✅ **React with Vite**
✅ **Real-time notifications**
✅ **Responsive design**
✅ **Task management**
✅ **Progress tracking**

## 🔄 Deployment Process

### 1. Update Environment Variables
Before deploying, update the frontend environment:

**Create `.env.production` in `focusguard-frontend/`:**
```env
VITE_API_URL=https://your-render-backend-url.onrender.com
```

### 2. Commit and Push
```bash
git add .
git commit -m "🚀 Prepare for deployment - BERT integration and enhanced features"
git push origin main
```

### 3. Monitor Deployment
- **Render**: Check build logs for BERT model downloads
- **Netlify**: Verify build completes successfully

## 🧪 Testing Deployment

### 1. Backend Health Check
```bash
curl https://your-render-backend-url.onrender.com/
```

### 2. Frontend Connection
- Open your Netlify URL
- Check browser console for connection status
- Test login functionality

### 3. BERT Functionality
- Create a focus session
- Test activity monitoring
- Verify notifications work

## 🔧 Troubleshooting

### Common Issues:

**1. BERT Models Not Loading**
- Check Render logs for model download errors
- Verify internet connectivity during build
- Models will download on first request if build fails

**2. WebSocket Connection Issues**
- Verify CORS settings in backend
- Check if WebSocket URL is correct
- Ensure backend is running

**3. MongoDB Connection**
- Verify connection string format
- Check IP whitelist in MongoDB Atlas
- Ensure database exists

**4. Build Failures**
- Check Python version compatibility
- Verify all dependencies in requirements.txt
- Monitor memory usage during build

### Performance Optimization:

**Backend:**
- BERT models use CPU only (GPU not available on Render)
- Models are cached in `/tmp` directory
- First request may be slow due to model loading

**Frontend:**
- Static assets are optimized by Vite
- Real-time updates via WebSocket
- Progressive loading for better UX

## 📊 Monitoring

### Render Dashboard:
- Monitor CPU and memory usage
- Check build logs for errors
- View request logs

### Netlify Dashboard:
- Monitor build status
- Check form submissions
- View analytics

## 🔐 Security

### Environment Variables:
- Never commit sensitive data
- Use Render's secure environment variables
- Rotate MongoDB credentials regularly

### CORS Configuration:
- Backend is configured for production domains
- WebSocket connections are secured
- API endpoints are protected

## 🎉 Success!

Once deployed, your FocusGuard application will be available at:
- **Frontend**: `https://your-netlify-site.netlify.app`
- **Backend**: `https://your-render-backend.onrender.com`

The application includes:
- ✅ AI-powered activity classification
- ✅ Real-time notifications
- ✅ Task and reminder management
- ✅ Progress tracking
- ✅ Custom audio support
- ✅ Responsive design

Happy coding! 🚀
