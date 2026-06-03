# 🚂 Railway Deployment Guide

## Quick Deploy Steps

### 1. **Push to GitHub**

```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit - AI Hiring Agent"

# Add your GitHub remote
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/hiring-agent.git
git push -u origin main
```

### 2. **Deploy to Railway**

1. **Go to [Railway.app](https://railway.app)**
2. **Sign up** with GitHub
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose your hiring-agent repository**

### 3. **Configure Environment Variables**

In Railway dashboard, go to **Variables** tab and add:

```
LLM_PROVIDER=gemini
DEFAULT_MODEL=gemini-2.5-flash
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 4. **Deploy!**

- Railway will automatically build and deploy
- You'll get a URL like: `https://your-app-name.up.railway.app`
- Deployment usually takes 3-5 minutes

## 🎉 That's it!

Your hiring agent will be live and accessible worldwide!

## 📊 Features Available on Railway:

✅ **Auto-scaling** - Handles traffic spikes  
✅ **Custom domains** - Use your own domain  
✅ **SSL certificates** - Automatic HTTPS  
✅ **Monitoring** - Built-in analytics  
✅ **Free tier** - $5 monthly credit  

## 🔧 Troubleshooting

**Build fails?**
- Check that all files are committed to GitHub
- Verify requirements.txt has all dependencies

**App crashes?**
- Check Railway logs in the dashboard
- Ensure GEMINI_API_KEY is set correctly

**API limits?**
- Users can use Demo Mode
- Consider upgrading to Gemini paid plan
- Add multiple API keys for rotation

## 💡 Pro Tips

1. **Monitor usage** in Railway dashboard
2. **Set up custom domain** for professional look
3. **Enable analytics** to track user engagement
4. **Consider paid Gemini plan** for higher limits