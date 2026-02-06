from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import time
from supabase import create_client, Client
import openai
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from google.cloud import videointelligence
import uvicorn
from tensorflow.keras.models import load_model
import numpy as np
from PIL import Image
import io

# Load environment variables
load_dotenv()

# Set Google Cloud credentials
if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Load Model
MODEL_PATH = "hear2sign_model.h5"
CLASS_NAMES = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
               'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 
               'del', 'nothing', 'space']
model = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "your-supabase-service-key")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "images")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-key")

# Create Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"Supabase client initialized with URL: {SUPABASE_URL}")
except Exception as e:
    print(f"Failed to initialize Supabase client: {e}")
    supabase = None

if OPENAI_API_KEY != "your-openai-key":
    openai.api_key = OPENAI_API_KEY

class VideoRequest(BaseModel):
    file_name: str
    file_data: str  # base64 encoded video data
    
    class Config:
        str_strip_whitespace = True

@app.get("/health")
async def health_check():
    return {
        "status": "ok", 
        "supabase_initialized": supabase is not None,
        "supabase_url": SUPABASE_URL,
        "bucket": SUPABASE_BUCKET
    }

@app.on_event("startup")
async def load_asl_model():
    global model
    try:
        model = load_model(MODEL_PATH)
        print("ASL Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")

@app.get("/get-video/{file_path:path}")
async def get_video(file_path: str):
    try:
        if supabase is None:
            raise HTTPException(status_code=500, detail="Supabase client not initialized")
        
        public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_path)
        return {"success": True, "video_url": public_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video: {str(e)}")

@app.post("/process-video")
async def process_video(request: VideoRequest):
    try:
        print(f"Received request: file_name={request.file_name}, data_length={len(request.file_data)}")
        
        # Check if Supabase is available
        if supabase is None:
            print("ERROR: Supabase client is None")
            raise HTTPException(status_code=500, detail="Supabase client not initialized")
        
        # 1. Upload video to Supabase
        print("Starting video upload to Supabase...")
        video_url = upload_video_to_supabase(request.file_name, request.file_data)
        print(f"Uploaded to: {video_url}")
        
        # 2. Transcribe video using Video Intelligence API
        print("Starting transcription...")
        try:
            transcript = transcribe_video(video_url)
        except Exception as e:
            print(f"Transcription failed: {e}")
            transcript = "Transcription unavailable"
        
        return {"success": True, "transcript": transcript, "video_url": video_url}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def upload_video_to_supabase(file_name: str, file_data: str) -> str:
    import base64
    
    if supabase is None:
        raise Exception("Supabase client not initialized")
    
    # Validate base64 data
    if not file_data:
        raise Exception("No file data provided")
    
    try:
        # Decode base64 file data
        video_bytes = base64.b64decode(file_data)
        print(f"Decoded video size: {len(video_bytes)} bytes")
        
        if len(video_bytes) == 0:
            raise Exception("Decoded video data is empty")
            
    except Exception as e:
        raise Exception(f"Invalid base64 data: {e}")
    
    # Upload to Supabase storage
    file_path = f"uploads/{int(time.time())}_{file_name}"
    
    try:
        result = supabase.storage.from_(SUPABASE_BUCKET).upload(
            file_path, video_bytes
        )
        print(f"Upload result: {result}")
        
        # Get public URL
        public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_path)
        return public_url
    except Exception as e:
        print(f"Supabase upload error: {e}")
        raise Exception(f"Failed to upload to Supabase: {e}")



def transcribe_video(video_url: str) -> str:
    try:
        print(f"Transcribing video from URL: {video_url}")
        
        # Download video content
        response = requests.get(video_url)
        response.raise_for_status()
        video_content = response.content
        print(f"Downloaded video content: {len(video_content)} bytes")
        
        client = videointelligence.VideoIntelligenceServiceClient()
        
        features = [videointelligence.Feature.SPEECH_TRANSCRIPTION]
        
        config = videointelligence.SpeechTranscriptionConfig(
            language_code="en-US",
            enable_automatic_punctuation=True,
        )
        
        video_context = videointelligence.VideoContext(
            speech_transcription_config=config
        )
        
        print("Sending video to Video Intelligence API...")
        operation = client.annotate_video(
            request={
                "features": features,
                "input_content": video_content,
                "video_context": video_context,
            }
        )
        
        print("Processing video transcription...")
        result = operation.result(timeout=300)
        print(f"Transcription complete. Results: {len(result.annotation_results)} annotations")
        
        transcript = ""
        for annotation_result in result.annotation_results:
            print(f"Speech transcriptions found: {len(annotation_result.speech_transcriptions)}")
            for speech_transcription in annotation_result.speech_transcriptions:
                print(f"Alternatives found: {len(speech_transcription.alternatives)}")
                for alternative in speech_transcription.alternatives:
                    print(f"Transcript: {alternative.transcript}")
                    transcript += alternative.transcript + " "
        
        result_text = transcript.strip() if transcript else "No speech detected"
        print(f"Final transcript: {result_text}")
        return result_text
    
    except Exception as e:
        print(f"Transcription error details: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Google Cloud Video Intelligence API error: {e}")
    
def predict_sign_from_data(file_data: str):
    """Decodes base64, preprocesses, and calls the TensorFlow model."""
    if model is None:
        return "Model not loaded", 0.0

    try:
        # 1. Decode base64 to image
        img_bytes = base64.b64decode(file_data)
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        
        # 2. Preprocess 
        img = img.resize((64, 64))
        img_array = np.array(img)
        img_array = np.expand_dims(img_array, axis=0) 

        # 4. Predict
        predictions = model.predict(img_array)
        score = predictions[0] 
        
        predicted_idx = np.argmax(score)
        label = CLASS_NAMES[predicted_idx]
        confidence = float(np.max(score))
        
        return label, confidence
    except Exception as e:
        print(f"Inference error: {e}")
        return "Error", 0.0

@app.post("/predict-sign")
async def predict_sign(request: VideoRequest):
    label, confidence = predict_sign_from_data(request.file_data)
    return {
        "success": True,
        "prediction": label,
        "confidence": f"{confidence * 100:.2f}%"
    }

# def generate_sign_images(text: str) -> list:
#     # Split text into words/phrases
#     words = text.split()
#     image_paths = []
#     
#     for word in words:
#         # Generate sign language image using DALL-E
#         response = openai.Image.create(
#             prompt=f"American Sign Language hand gesture for the word '{word}', clean white background, professional photo",
#             n=1,
#             size="512x512"
#         )
#         
#         # Download image
#         img_url = response['data'][0]['url']
#         img_response = requests.get(img_url)
#         
#         img_path = f"sign_{word}_{int(time.time())}.png"
#         with open(img_path, 'wb') as f:
#             f.write(img_response.content)
#         
#         image_paths.append(img_path)
#     
#     return image_paths

# def create_sign_video(image_paths: list) -> str:
#     # Create video from images
#     output_video = f"sign_video_{int(time.time())}.mp4"
#     
#     # Create image list file for ffmpeg
#     with open('images.txt', 'w') as f:
#         for img_path in image_paths:
#             f.write(f"file '{img_path}'\n")
#             f.write("duration 1\n")  # 1 second per image
#     
#     # Create video
#     subprocess.run([
#         "ffmpeg", "-f", "concat", "-safe", "0", "-i", "images.txt",
#         "-vf", "fps=1", "-pix_fmt", "yuv420p", output_video, "-y"
#     ])
#     
#     return output_video

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)