# Video Processor with AI Analysis

A Python tool that downloads videos and analyzes them using Google AI Studio (Gemini). Provides comprehensive scene-by-scene analysis with timestamps, perfect for understanding video content structure.

## Features

- Download videos from TikTok, Instagram, and other platforms using yt-dlp
- Multi-scene AI analysis using Google Gemini 2.5 Pro
- Frame-by-frame content analysis with timestamps
- Support for single video or batch processing
- Comprehensive metadata output in JSON format
- Scene breakdown with visual elements, audio analysis, and engagement metrics

## Requirements

- Python 3.7+
- yt-dlp
- Google AI Studio API key

## Installation

1. Install dependencies:
```bash
pip install google-genai python-dotenv
```

2. Install yt-dlp:
```bash
pip install yt-dlp
```

3. Create `.env` file with your Google AI Studio API key:
```
GEMINI_API_KEY=your_api_key_here
```

## Usage

### Process Single Video (Quick Test)
```bash
python video_processor.py --single-link "https://www.tiktok.com/@user/video/123456789"
```

### Process Multiple Videos from File
1. Create `links.txt` with video URLs (one per line):
```
https://www.tiktok.com/@user1/video/123
https://www.instagram.com/reel/abc123
```

2. Run batch processing:
```bash
python video_processor.py --links-file links.txt
```

### Command Line Options
```bash
python video_processor.py [options]

Options:
  -s, --single-link URL     Process a single video URL
  -l, --links-file FILE     Process URLs from file (default: links.txt)
  -o, --output-dir DIR      Output directory for videos (default: downloads)
  -h, --help               Show help message
```

## Output

### Video Files
Downloaded to `downloads/` folder with original titles

### Metadata Files
- **Single video**: `single_video_metadata.json`
- **Batch processing**: `metadata.json`

### Analysis Structure
```json
{
  "video_summary": "Brief overview of the entire video",
  "total_duration": "Video length in seconds",
  "content_type": "dance, comedy, tutorial, etc.",
  "overall_mood": "Emotional tone",
  "scenes": [
    {
      "scene_number": 1,
      "start_timestamp": "0:00",
      "duration": "3.5s",
      "description": "What's happening in this scene",
      "text_overlay": "Visible text or captions",
      "main_action": "Primary focus",
      "visual_elements": "Colors, lighting, etc."
    }
  ],
  "audio_elements": {
    "music_type": "Background music description",
    "voice_over": true,
    "sound_effects": "Notable audio"
  },
  "visual_style": {
    "camera_work": "Movement and style",
    "setting": "Location/environment",
    "production_quality": "Low/Medium/High"
  },
  "engagement_elements": ["hooks", "transitions"],
  "suggested_tags": ["relevant", "keywords"],
  "platform_indicators": "TikTok/Instagram watermarks"
}
```

## Examples

### Single Video Analysis
```bash
python video_processor.py -s "https://www.tiktok.com/@example/video/123"
```

### Custom Output Directory
```bash
python video_processor.py -l my_links.txt -o custom_downloads
```

### Batch Processing
```bash
# Create links file
cat > links.txt << EOF
https://www.tiktok.com/@user1/video/123
https://www.tiktok.com/@user2/video/456
EOF

# Process all videos
python video_processor.py
```

## Dependencies

The script automatically checks for required dependencies:
- `yt-dlp` for video downloading
- `google-genai` for AI analysis
- `python-dotenv` for environment variables

## License

MIT License