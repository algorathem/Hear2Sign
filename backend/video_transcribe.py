import boto3
import time
import subprocess
import requests
import os

def transcribe_video_to_text(video_file, bucket_name):
    # Extract audio
    audio_file = "extracted_audio.wav"
    subprocess.run([
        "ffmpeg", "-i", video_file, "-vn", "-acodec", "pcm_s16le", 
        "-ar", "16000", "-ac", "1", audio_file, "-y"
    ])
    
    # Create S3 bucket if it doesn't exist
    s3 = boto3.client('s3')
    try:
        s3.head_bucket(Bucket=bucket_name)
    except:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'us-west-2'}
        )
    
    # Upload to S3
    audio_key = f"audio/{audio_file}"
    s3.upload_file(audio_file, bucket_name, audio_key)
    
    # Start transcription
    transcribe = boto3.client('transcribe')
    job_name = f"transcription-{int(time.time())}"
    
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': f's3://{bucket_name}/{audio_key}'},
        MediaFormat='wav',
        LanguageCode='en-US'
    )
    
    # Wait for completion
    while True:
        response = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        status = response['TranscriptionJob']['TranscriptionJobStatus']
        if status == 'COMPLETED':
            transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
            break
        elif status == 'FAILED':
            raise Exception("Transcription failed")
        time.sleep(10)
    
    # Get transcript
    transcript_response = requests.get(transcript_uri)
    transcript_data = transcript_response.json()
    
    # Cleanup
    os.remove(audio_file)
    
    return transcript_data['results']['transcripts'][0]['transcript']

# Usage example
if __name__ == "__main__":
    video_file = "your_video.mp4"  # Replace with your video file
    bucket_name = "hear2sign-transcribe-bucket"  # Will be created automatically
    
    text = transcribe_video_to_text(video_file, bucket_name)
    print(text)