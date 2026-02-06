import boto3
import subprocess
import os
import time
import json

def extract_audio(video_path, audio_path):
    subprocess.run([
        'ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', 
        '-ar', '16000', '-ac', '1', audio_path, '-y'
    ], check=True)

def upload_to_s3(file_path, bucket, key):
    s3 = boto3.client('s3')
    s3.upload_file(file_path, bucket, key)
    return f's3://{bucket}/{key}'

def transcribe_audio(media_uri, job_name):
    transcribe = boto3.client('transcribe')
    
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': media_uri},
        MediaFormat='wav',
        LanguageCode='en-US'
    )
    
    while True:
        response = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        status = response['TranscriptionJob']['TranscriptionJobStatus']
        
        if status == 'COMPLETED':
            return response['TranscriptionJob']['Transcript']['TranscriptFileUri']
        elif status == 'FAILED':
            raise Exception("Transcription failed")
        
        time.sleep(10)

def get_transcript_text(transcript_uri):
    import urllib.request
    with urllib.request.urlopen(transcript_uri) as response:
        data = json.loads(response.read())
        return data['results']['transcripts'][0]['transcript']

def video_to_text(video_path, s3_bucket):
    audio_path = 'temp_audio.wav'
    extract_audio(video_path, audio_path)
    
    s3_key = f"audio/{os.path.basename(audio_path)}"
    media_uri = upload_to_s3(audio_path, s3_bucket, s3_key)
    
    job_name = f"transcribe-{int(time.time())}"
    transcript_uri = transcribe_audio(media_uri, job_name)
    
    text = get_transcript_text(transcript_uri)
    
    os.remove(audio_path)
    
    return text

if __name__ == "__main__":
    video_file = "your_video.mp4"
    bucket_name = "your-s3-bucket"
    
    try:
        transcript = video_to_text(video_file, bucket_name)
        print("Transcript:")
        print(transcript)
        
        with open("transcript.txt", "w") as f:
            f.write(transcript)
        print("\nTranscript saved to transcript.txt")
        
    except Exception as e:
        print(f"Error: {e}")
