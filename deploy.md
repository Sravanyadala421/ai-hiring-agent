# Deployment Guide

## 🌐 Web Application (Current)

Your hiring agent is now running as a web application:

- **Local:** http://localhost:8501
- **Network:** http://192.168.0.9:8501

## 🐳 Docker Deployment

### Build and run with Docker:

```bash
# Build the image
docker build -t hiring-agent .

# Run the container
docker run -p 8501:8501 -e GEMINI_API_KEY=your_api_key_here hiring-agent
```

### Or use Docker Compose:

```bash
# Set your API key in environment
export GEMINI_API_KEY=your_actual_api_key

# Run with docker-compose
docker-compose up -d
```

## ☁️ Cloud Deployment Options

### 1. Railway (Recommended - Easy)

1. Push your code to GitHub
2. Go to [Railway.app](https://railway.app)
3. Connect your GitHub repo
4. Add environment variable: `GEMINI_API_KEY`
5. Deploy automatically

### 2. Heroku

1. Install Heroku CLI
2. Create `runtime.txt` with `python-3.11`
3. Create `Procfile` with `web: streamlit run app.py --server.port=$PORT`
4. Deploy:
```bash
heroku create your-hiring-agent
heroku config:set GEMINI_API_KEY=your_api_key
git push heroku main
```

### 3. Streamlit Cloud (Free)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Add secrets in the Streamlit dashboard
5. Deploy automatically

### 4. Google Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT/hiring-agent

# Deploy to Cloud Run
gcloud run deploy --image gcr.io/YOUR_PROJECT/hiring-agent --platform managed
```

### 5. AWS App Runner

1. Push Docker image to ECR
2. Create App Runner service
3. Configure environment variables
4. Deploy

## 🔧 Environment Variables

Make sure to set these for cloud deployment:

```
LLM_PROVIDER=gemini
DEFAULT_MODEL=gemini-2.5-flash
GEMINI_API_KEY=your_actual_api_key_here
```

## 📊 Production Considerations

1. **Scaling:** Use load balancers for high traffic
2. **Security:** Enable HTTPS and secure API keys
3. **Monitoring:** Add application monitoring
4. **Database:** Consider persistent storage for evaluation history
5. **Caching:** Optimize for faster resume processing

## 🔒 Security Notes

- Never commit API keys to version control
- Use environment variables or secret managers
- Enable HTTPS in production
- Consider rate limiting for public deployments