# QR Studio

A modern, full-stack QR code generator with advanced styling capabilities and logo integration.

## Features

- 🎨 **Advanced Styling**: 6 module styles (square, rounded, dots, gapped, bars) with custom colors
- 🖼️ **Logo Integration**: Upload logos with smart positioning and background customization
- ⚙️ **Flexible Configuration**: Error correction levels, eye shapes/styles, corner rounding
- 🎯 **Quick Presets**: 6 built-in presets (Classic, Modern, Dots, Retro, Dark, Neon)
- 🚀 **High Performance**: FastAPI backend with optimized image processing
- 💻 **Modern UI**: React + TypeScript frontend with shadcn/ui components
- 📱 **Responsive**: Works seamlessly on desktop, tablet, and mobile
- 🔗 **API-First**: RESTful API for easy integration

## Quick Start

### Development

```bash
# Clone the repository
git clone <repository-url>
cd qr-studio

# Start with Docker Compose (recommended)
docker-compose up -d

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Manual Setup:**

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Production

```bash
# Production deployment (coming soon)
docker-compose -f docker-compose.prod.yml up -d
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

## Tech Stack

- **Backend**: FastAPI, Python, Pillow, qrcode, Pydantic
- **Frontend**: React, TypeScript, Vite, shadcn/ui, Tailwind CSS
- **Development**: Docker Compose, Redis
- **Type Safety**: TypeScript (frontend), mypy (backend - planned)

## License

MIT License
