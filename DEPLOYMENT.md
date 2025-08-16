# 🚀 QR Studio - Free Deployment Guide

Deploy QR Studio using **100% free services** - no credit card required!

## 🎯 Quick Deployment (20 minutes)

### **Backend: Railway.app (Recommended)**

1. **Sign up**: [railway.app](https://railway.app) with GitHub
2. **New Project** → **Deploy from GitHub repo** → Select your QR Studio repo
3. **Add PostgreSQL**: New Service → Database → PostgreSQL
4. **Add Redis**: New Service → Database → Redis
5. **Configure backend service**:

   ```
   Root Directory: backend
   Start Command: gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
   ```

6. **Set environment variables**:
   ```bash
   SECRET_KEY=<generate-32-char-hex>
   ADMIN_TOKEN=<generate-32-char-hex>
   ENV=production
   CORS_ORIGINS=https://yourusername.github.io
   REDIS_URL=${{Redis.REDIS_URL}}
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ```

### **Frontend: GitHub Pages**

1. **Repository Settings** → **Pages** → **Source: GitHub Actions**
2. **Add GitHub Secret**: `VITE_API_URL` = `https://your-app.railway.app`
3. **Push to main** - GitHub Actions will deploy automatically

### **Generate Secure Secrets**

```bash
# Generate secure secrets
SECRET_KEY=$(openssl rand -hex 32)
ADMIN_TOKEN=$(openssl rand -hex 32)

echo "SECRET_KEY: $SECRET_KEY"
echo "ADMIN_TOKEN: $ADMIN_TOKEN"
```

## 🔄 Alternative: Render.com

If Railway doesn't work, use Render.com:

1. **Sign up**: [render.com](https://render.com) with GitHub
2. **New Blueprint** → Connect GitHub repo
3. Services auto-created from `render.yaml`
4. **Add secrets** in Render dashboard:
   - `SECRET_KEY`
   - `ADMIN_TOKEN`

## ✅ Verify Deployment

```bash
# Check backend health
curl https://your-app.railway.app/health

# Test QR generation
curl -X POST "https://your-app.railway.app/api/v1/qr/generate-form" \
  -F "url=https://example.com"

# Visit your app
open https://yourusername.github.io/qr-studio/
```

## 🛡️ Security & Abuse Protection

QR Studio includes built-in protection against abuse:

- **Rate limiting**: 50 QR codes per hour per IP
- **File size limits**: 5MB max logo uploads
- **Request throttling**: 3 concurrent requests per IP
- **Admin monitoring**: `/admin/stats` endpoint

## 💰 Cost Breakdown

| Service        | Free Tier       | Usage              |
| -------------- | --------------- | ------------------ |
| Railway.app    | $5 credit/month | ~$2-3/month        |
| GitHub Pages   | Unlimited       | 100GB bandwidth    |
| GitHub Actions | 2000 min/month  | ~50 min/month      |
| **Total**      | **$0/month**    | Within free limits |

## 🔧 Environment Variables

### Required

- `SECRET_KEY`: 32-character hex string
- `ADMIN_TOKEN`: 32-character hex string
- `ENV`: `production`
- `CORS_ORIGINS`: Your frontend URL

### Optional (with defaults)

- `DAILY_QR_LIMIT`: `500` (QR codes per day per IP)
- `HOURLY_QR_LIMIT`: `50` (QR codes per hour per IP)
- `MAX_FILE_SIZE`: `5242880` (5MB)

## 🚨 Troubleshooting

**Backend not starting?**

- Check Railway logs for errors
- Verify all environment variables are set
- Ensure `CORS_ORIGINS` matches your frontend URL

**Frontend can't connect to backend?**

- Verify `VITE_API_URL` GitHub secret
- Check CORS configuration
- Ensure backend is deployed and healthy

**Getting rate limited?**

- Check admin dashboard: `https://your-app.railway.app/admin/stats`
- Adjust limits in environment variables if needed

## 📚 Additional Resources

- **API Documentation**: `https://your-app.railway.app/docs`
- **Admin Dashboard**: `https://your-app.railway.app/admin/stats`
- **Health Check**: `https://your-app.railway.app/health`

---

**🎉 Your QR Studio is now live and free forever!**

Total setup time: ~20 minutes  
Monthly cost: $0  
Scalability: Ready to grow
