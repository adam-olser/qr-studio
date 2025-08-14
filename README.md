# QR Studio

A modern, full-stack QR code generator with advanced styling capabilities and logo integration.

## Features

- 🎨 **Advanced Styling**: Multiple module styles (square, rounded, dots, gapped)
- 🖼️ **Logo Integration**: Embed logos with customizable positioning and backgrounds
- 🔧 **Flexible Configuration**: Error correction levels, eye shapes, corner rounding
- 🚀 **High Performance**: FastAPI backend with optimized image processing
- 🎯 **Modern UI**: React frontend with shadcn/ui components
- 📱 **Responsive**: Works on desktop, tablet, and mobile
- 🔗 **API-First**: Easy integration with other services

## Quick Start

### Development

```bash
# Clone the repository
git clone <repository-url>
cd qr-studio

# Start with Docker Compose
docker-compose up -d

# Or run separately:

# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## API Usage

```typescript
// Generate QR code
const response = await fetch('/api/v1/qr/generate', {
  method: 'POST',
  body: formData // includes URL, logo, and options
})

const qrImage = await response.blob()
```

## Tech Stack

- **Backend**: FastAPI, Python, Pillow, qrcode
- **Frontend**: React, TypeScript, Vite, shadcn/ui, Tailwind CSS
- **Infrastructure**: Docker, Redis (caching), S3 (storage)

## License

MIT License
