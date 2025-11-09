# AI Image Captioning - Description Generator

Bu proje, görüntüleri analiz edip kısa ve uzun açıklamalar üreten bir API sunar.

## Backend Çalıştırma

Backend uygulamasını çalıştırmak için iki yöntem vardır:

### 1. Python Modülü Olarak Çalıştırma (Önerilen)

```bash
# Proje kök dizininde:
python -m backend.app
```

### 2. Doğrudan Script Olarak Çalıştırma

```bash
# backend/ dizininde:
python app.py
```

## API Endpoints

- `GET /health` - API durumunu kontrol eder
- `POST /api/caption` - Görüntü yükleyip açıklama üretir
- `GET /api/history` - Önceki açıklamaları listeler
- `GET /images/<filename>` - Yüklenmiş görselleri servis eder