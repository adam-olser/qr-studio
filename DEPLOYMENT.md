# 🚀 QR Studio - Free Deployment Guide

Deploy QR Studio using **100% free services** - no credit card required!

## 🎯 Quick Deployment (20 minutes)

### **Backend: Render.com (Recommended - Free Forever)**

1. **Sign up**: [render.com](https://render.com) with GitHub
2. **New Blueprint** → Connect your QR Studio repository
3. **Services auto-created** from `render.yaml` file
4. **Add secrets** in Render dashboard:
   - `SECRET_KEY`: Generate with `openssl rand -hex 32`
   - `ADMIN_TOKEN`: Generate with `openssl rand -hex 32`

**Note**: Services sleep after 15min inactivity (30-60s cold start)

### **Frontend: GitHub Pages**

1. **Repository Settings** → **Pages** → **Source: GitHub Actions**
2. **Add GitHub Secret**: `VITE_API_URL` = `https://your-backend-name.onrender.com`
3. **Push to main** - GitHub Actions will deploy automatically

### **Generate Secure Secrets**

```bash
# Generate and copy these to Render dashboard
openssl rand -hex 32  # Use for SECRET_KEY
openssl rand -hex 32  # Use for ADMIN_TOKEN
```

## 🔄 Alternative: Fly.io + Supabase

For better performance (no cold starts):

1. **Backend on Fly.io**: Install flyctl, launch app, set secrets
2. **Database on Supabase**: Create project, get connection URL
3. **Cost**: ~$5/month (no cold starts, better performance)

## ✅ Verify Deployment

```bash
# Check backend health
curl https://your-backend-name.onrender.com/health

# Test QR generation
curl -X POST "https://your-backend-name.onrender.com/api/v1/qr/generate-form" \
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

| Service        | Free Tier    | Usage              |
| -------------- | ------------ | ------------------ |
| Render.com     | FREE Forever | 750 hours/month    |
| GitHub Pages   | FREE Forever | 100GB bandwidth    |
| GitHub Actions | FREE Forever | 2000 min/month     |
| **Total**      | **$0/month** | Truly free forever |

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

- Check Render logs for errors
- Verify all environment variables are set
- Ensure `CORS_ORIGINS` matches your frontend URL

**Frontend can't connect to backend?**

- Verify `VITE_API_URL` GitHub secret
- Check CORS configuration
- Ensure backend is deployed and healthy

**Getting rate limited?**

- Check admin dashboard: `https://your-backend-name.onrender.com/admin/stats`
- Adjust limits in environment variables if needed

## 📚 Additional Resources

- **API Documentation**: `https://your-backend-name.onrender.com/docs`
- **Admin Dashboard**: `https://your-backend-name.onrender.com/admin/stats`
- **Health Check**: `https://your-backend-name.onrender.com/health`

---

**🎉 Your QR Studio is now live and free forever!**

Total setup time: ~20 minutes  
Monthly cost: $0  
Scalability: Ready to grow
