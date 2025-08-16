# QR Studio - Quick Start Guide

## 🚀 Start the Application

### Option 1: Docker Compose (Recommended)

```bash
cd /Users/adamolser/kiwidev/qr-studio
docker-compose up -d
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

#### Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend:

```bash
cd frontend
npm install
npm run dev
```

## 🧪 Test the Application

1. **Open**: http://localhost:3000
2. **Enter URL**: Try "https://kiwicom.github.io"
3. **Add Logo**: Upload the Kiwi logo from `docs/kiwicom.png`
4. **Try Presets**: Click "Modern" or "iOS" preset buttons
5. **Generate & Download**: Click "Generate QR" then "Download"

## 🔗 API Integration

Replace the static QR in your Kiwi.com code:

```typescript
// Instead of static QR image
const qrUrl = `http://localhost:8000/api/qr/generate-form`;

// POST with form data:
const formData = new FormData();
formData.append("url", deepLinkUrl);
formData.append("style", "modern");
// Add logo file if needed
```

## ✨ Features Working

- ✅ URL validation and real-time preview
- ✅ Logo upload with drag & drop
- ✅ 5 preset styles (Classic, Modern, Dots, iOS, Minimal)
- ✅ Custom QR styling (colors, shapes, sizes)
- ✅ Error handling and loading states
- ✅ Download functionality
- ✅ Responsive design
- ✅ Professional API with validation

## 🛠️ Next Steps (Optional)

- Add more preset styles
- Implement batch QR generation
- Add user accounts and saved presets
- Deploy to production environment
