# Hear2Sign

Video to Sign Language Converter

## Project Structure

```
Hear2Sign/
├── frontend/           # React frontend application
│   ├── src/
│   │   ├── index.js
│   │   └── VideoToSignLanguage.jsx
│   ├── public/
│   │   └── index.html
│   ├── package.json
│   └── package-lock.json
│
├── backend/            # Python backend API
│   ├── backend_api.py          # FastAPI server (Google Cloud Speech)
│   ├── video_transcribe.py     # AWS Transcribe implementation
│   ├── video_to_text.py        # AWS Transcribe standalone script
│   ├── backend_requirements.txt
│   └── requirements.txt
│
├── .env                # Environment variables
└── hear2sign-9fce27860301.json  # Google Cloud credentials
```

## Setup

### Frontend
```bash
cd frontend
npm install
npm start
```

### Backend
```bash
cd backend
pip install -r backend_requirements.txt
python backend_api.py
```

## Backend Files

- **backend_api.py**: Main FastAPI server using Google Cloud Speech-to-Text
- **video_transcribe.py**: AWS Transcribe implementation (alternative)
- **video_to_text.py**: Standalone AWS Transcribe script

## API Endpoint

- POST `http://localhost:8000/process-video`
  - Accepts video file (base64 encoded)
  - Returns transcript text
