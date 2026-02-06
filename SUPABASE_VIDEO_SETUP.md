# Supabase Video Storage Setup

## What's Implemented

✅ **Backend**: Videos are uploaded to Supabase Storage and URLs are returned
✅ **Frontend**: Videos play directly from Supabase using the public URL
✅ **API Endpoint**: GET `/get-video/{file_path}` to retrieve any video URL

## Supabase Configuration Required

### 1. Create Storage Bucket
1. Go to your Supabase Dashboard → Storage
2. Create a bucket named `images` (or update `SUPABASE_BUCKET` in `.env`)
3. Make the bucket **PUBLIC** for video playback

### 2. Set Bucket Policies
Make sure your bucket allows public read access:

```sql
-- Allow public read access
CREATE POLICY "Public Access"
ON storage.objects FOR SELECT
USING ( bucket_id = 'images' );

-- Allow authenticated uploads
CREATE POLICY "Authenticated Upload"
ON storage.objects FOR INSERT
WITH CHECK ( bucket_id = 'images' );
```

### 3. Environment Variables
Update your `.env` file:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_BUCKET=images
```

## How It Works

1. **Upload**: User selects video → Frontend sends base64 to backend
2. **Store**: Backend uploads to Supabase Storage → Returns public URL
3. **Play**: Frontend uses Supabase URL in `<video>` tag → Video plays directly

## API Endpoints

### POST `/process-video`
Uploads video, transcribes, and returns URL
```json
{
  "file_name": "video.mp4",
  "file_data": "base64_encoded_video"
}
```

Response:
```json
{
  "success": true,
  "transcript": "transcribed text...",
  "video_url": "https://your-project.supabase.co/storage/v1/object/public/images/uploads/..."
}
```

### GET `/get-video/{file_path}`
Retrieves public URL for any uploaded video
```
GET /get-video/uploads/1234567890_video.mp4
```

Response:
```json
{
  "success": true,
  "video_url": "https://your-project.supabase.co/storage/v1/object/public/images/uploads/..."
}
```

## Benefits

- ✅ Videos persist across sessions
- ✅ No local storage needed
- ✅ Scalable cloud storage
- ✅ Direct video streaming from CDN
- ✅ Shareable video URLs
