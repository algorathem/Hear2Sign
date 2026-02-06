import React, { useState } from 'react';

function VideoToSignLanguage() {
  const [posts, setPosts] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [contentType, setContentType] = useState('sign');
  const API_BASE_URL = 'https://hear2sign.onrender.com';
  
  const publishContent = async (file) => {
    if (!file.type.startsWith('video/')) {
      alert('Please select a valid video file');
      return;
    }
    
    if (file.size > 100 * 1024 * 1024) {
      alert('File size too large. Please select a video under 100MB');
      return;
    }
    
    setUploading(true);
    
    const reader = new FileReader();
    reader.onload = async () => {
      const videoUrl = reader.result;
      const base64Data = reader.result.split(',')[1];
      
      try {
        const endpoint = contentType === 'sign' 
    ? 'API_BASE_URL/predict-sign' 
    : 'API_BASE_URL/process-video';
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            file_name: file.name,
            file_data: base64Data 
          })
        });

        if (!response.ok) throw new Error('Processing failed');
        
        const result = await response.json();
        
       if (result.success) {
       setPosts([{id: Date.now(), type: contentType, videoUrl: result.video_url || URL.createObjectURL(file), transcript: result.prediction || result.transcript || "No text detected", timestamp: new Date().toLocaleString()}, ...posts]);
        } else {
          throw new Error(result.error || 'Processing failed');
        }
      } catch (error) {
        alert('Upload failed: ' + error.message);
      }
      
      setUploading(false);
    };
    
    reader.readAsDataURL(file);
  };

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', padding: '40px 20px' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', color: 'white', marginBottom: '50px' }}>
          <h1 style={{ fontSize: '48px', fontWeight: '700', marginBottom: '10px', textShadow: '2px 2px 4px rgba(0,0,0,0.2)' }}>🤟 Hear2Sign</h1>
          <p style={{ fontSize: '20px', opacity: '0.95' }}>Making content accessible for everyone</p>
        </div>
        
        <div style={{ background: 'white', borderRadius: '20px', padding: '40px', boxShadow: '0 20px 60px rgba(0,0,0,0.3)', marginBottom: '40px' }}>
          <h3 style={{ fontSize: '24px', marginBottom: '25px', color: '#333' }}>📤 Upload Video</h3>
          
          <div style={{ marginBottom: '25px', display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', padding: '12px 20px', borderRadius: '12px', background: contentType === 'sign' ? '#667eea' : '#f0f0f0', color: contentType === 'sign' ? 'white' : '#333', transition: 'all 0.3s', fontWeight: '500' }}>
              <input type="radio" value="sign" checked={contentType === 'sign'} onChange={(e) => setContentType(e.target.value)} style={{ marginRight: '10px' }} />
              🤟 Sign Language Video
            </label>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', padding: '12px 20px', borderRadius: '12px', background: contentType === 'audio' ? '#667eea' : '#f0f0f0', color: contentType === 'audio' ? 'white' : '#333', transition: 'all 0.3s', fontWeight: '500' }}>
              <input type="radio" value="audio" checked={contentType === 'audio'} onChange={(e) => setContentType(e.target.value)} style={{ marginRight: '10px' }} />
              🔊 Regular Video
            </label>
          </div>
          
          <div style={{ position: 'relative' }}>
            <input
              type="file"
              accept="video/*"
              onChange={(e) => e.target.files[0] && publishContent(e.target.files[0])}
              disabled={uploading}
              style={{ display: 'none' }}
              id="fileInput"
            />
            <label htmlFor="fileInput" style={{ display: 'block', padding: '20px', border: '3px dashed #667eea', borderRadius: '12px', textAlign: 'center', cursor: uploading ? 'not-allowed' : 'pointer', background: uploading ? '#f5f5f5' : '#fafafa', transition: 'all 0.3s' }}>
              <div style={{ fontSize: '48px', marginBottom: '10px' }}>📹</div>
              <div style={{ fontSize: '18px', color: '#667eea', fontWeight: '600' }}>
                {uploading ? 'Processing...' : 'Click to select video'}
              </div>
              <div style={{ fontSize: '14px', color: '#999', marginTop: '5px' }}>Max size: 100MB</div>
            </label>
          </div>
          
          {uploading && (
            <div style={{ marginTop: '20px', padding: '15px', background: '#e3f2fd', borderRadius: '8px', color: '#1976d2', textAlign: 'center', fontWeight: '500' }}>
              ⏳ Processing and transcribing your video...
            </div>
          )}
        </div>

        <h2 style={{ color: 'white', fontSize: '32px', marginBottom: '30px', textAlign: 'center' }}>📚 Published Content</h2>
        {posts.length === 0 ? (
          <div style={{ background: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)', borderRadius: '20px', padding: '60px', textAlign: 'center', color: 'white' }}>
            <div style={{ fontSize: '64px', marginBottom: '20px' }}>🎬</div>
            <p style={{ fontSize: '20px', opacity: '0.9' }}>No content yet. Be the first to publish!</p>
          </div>
        ) : (
          posts.map(post => (
            <div key={post.id} style={{ background: 'white', borderRadius: '20px', padding: '30px', marginBottom: '30px', boxShadow: '0 10px 30px rgba(0,0,0,0.2)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '10px' }}>
                <span style={{ background: post.type === 'sign' ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white', padding: '8px 20px', borderRadius: '20px', fontSize: '14px', fontWeight: '600' }}>
                  {post.type === 'sign' ? '🤟 Sign Language' : '🔊 Audio/Video'}
                </span>
                <span style={{ color: '#999', fontSize: '14px' }}>🕒 {post.timestamp}</span>
              </div>
              
              <video src={post.videoUrl} controls style={{ width: '100%', borderRadius: '12px', marginBottom: '20px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
              
              <div style={{ background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)', padding: '20px', borderRadius: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
                  <span style={{ fontSize: '20px', marginRight: '10px' }}>📝</span>
                  <strong style={{ fontSize: '18px', color: '#333' }}>Transcript</strong>
                </div>
                <p style={{ marginTop: '10px', lineHeight: '1.8', color: '#555', fontSize: '16px' }}>{post.transcript}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default VideoToSignLanguage;