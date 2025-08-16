# QR Studio

A modern, full-stack QR code generator with advanced styling capabilities and logo integration.

## ✨ Features

- 🎨 **Advanced Styling**: 6 module styles with custom colors and eye shapes
- 🖼️ **Logo Integration**: Upload and position logos with smart background handling
- 🎯 **Quick Presets**: 6 built-in styles (Classic, Modern, Dots, Retro, Dark, Neon)
- 📱 **Responsive Design**: Works seamlessly across all devices
- 🚀 **High Performance**: Optimized image processing with abuse protection
- 🔗 **API-First**: RESTful API for easy integration

## Quick Start

### Development

```bash
# Clone and start with Docker (recommended)
git clone <repository-url>
cd qr-studio
docker-compose up -d

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/docs
```

**Manual Setup:**
```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend && npm install && npm run dev
```

### 🚀 Production Deployment

Deploy for **FREE** using GitHub and Render.com:

```bash
# 1. Fork this repository
# 2. Enable GitHub Pages (Settings → Pages → GitHub Actions)
# 3. Deploy backend to Render.com using render.yaml
# 4. Add environment variables in Render dashboard

# See DEPLOYMENT.md for detailed instructions
```

## API Usage

### Generate QR Code

```bash
curl -X POST "http://localhost:8000/api/v1/qr/generate-form" \
  -F "url=https://example.com" \
  -F "style=rounded" \
  -F "dark_color=#000000" \
  -F "light_color=#FFFFFF" \
  -F "size=1024" \
  -F "logo=@logo.png"
```

### Get Available Presets

```bash
curl "http://localhost:8000/api/v1/qr/presets"
```

### Validate URL

```bash
curl "http://localhost:8000/api/v1/qr/validate-url?url=https://example.com"
```

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python, Pillow, qrcode, Redis
- **Frontend**: React, TypeScript, Vite, shadcn/ui, Tailwind CSS
- **Deployment**: GitHub Actions, Render.com, GitHub Pages
- **Testing**: Vitest, pytest, mypy

## 📖 Documentation

- **[Deployment Guide](DEPLOYMENT.md)** - Free deployment instructions
- **API Docs**: Available at `/docs` endpoint
- **Live Demo**: [QR Studio](https://adam-olser.github.io/qr-studio/)

## License

MIT License
