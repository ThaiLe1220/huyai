# HuyAI - Video Analysis & TikTok Channel Discovery

A Python toolkit for downloading videos, analyzing content with AI, and discovering TikTok pet channels. Combines video processing with Google Gemini 2.5 Pro and channel research with OpenAI GPT-4.1

## Tools

### 1. Video Processor (`video_processor.py`)
- Download videos from TikTok, Instagram, and other platforms using yt-dlp
- Multi-scene AI analysis using Google Gemini 2.5 Pro
- Frame-by-frame content analysis with timestamps
- Support for single video or batch processing
- Comprehensive metadata output in JSON format
- Scene breakdown with visual elements, audio analysis, and engagement metrics

### 2. TikTok Channel Finder (`tiktok_channel_finder.py`)
- Find popular TikTok pet and animal channels using GPT-4.1
- Keyword-based search with country targeting
- CSV database with duplicate prevention
- Track channel discovery history and metadata

## Requirements

- Python 3.7+
- yt-dlp
- Google AI Studio API key (for video analysis)
- OpenAI API key (for channel finding)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
pip install openai  # for channel finder
```

2. Create `.env` file with API keys:
```
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here
```

## Usage

### Video Processor

#### Process Single Video
```bash
python video_processor.py --single-link "https://www.tiktok.com/@user/video/123456789"
```

#### Process Multiple Videos from File
1. Create `links.txt` with video URLs (one per line)
2. Run batch processing:
```bash
python video_processor.py --links-file links.txt
```

#### Video Processor Options
```bash
python video_processor.py [options]

Options:
  -s, --single-link URL     Process a single video URL
  -l, --links-file FILE     Process URLs from file (default: links.txt)
  -o, --output-dir DIR      Output directory for videos (default: downloads)
  -h, --help               Show help message
```

### TikTok Channel Finder

#### Find Pet Channels
```bash
python tiktok_channel_finder.py -k "trending pets, viral animals, 2025" -c US
```

#### Channel Finder Options
```bash
python tiktok_channel_finder.py [options]

Options:
  -k, --keywords TEXT       Search keywords (comma-separated)
  -t, --target NUMBER       Number of channels to find (default: 20)
  -c, --country COUNTRY     Country targeting: US, IN, ID, BD, VN (default: US)
  -h, --help               Show help message
```

## Output

### Video Processor Output
- **Video Files**: Downloaded to `downloads/` folder with original titles
- **Metadata Files**: 
  - Single video: `single_video_metadata.json`
  - Batch processing: `metadata.json`

### TikTok Channel Finder Output
- **CSV Database**: `pet_channels.csv` with channel info and search history

### Video Analysis Structure
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

### Video Processing Examples
```bash
# Single video analysis
python video_processor.py -s "https://www.tiktok.com/@example/video/123"

# Custom output directory
python video_processor.py -l my_links.txt -o custom_downloads

# Batch processing from links file
python video_processor.py
```

### Channel Finding Examples
```bash
# Find dog channels
python tiktok_channel_finder.py --keywords "dogs, puppies" --target 25

# Find channels in specific country
python tiktok_channel_finder.py --keywords "pets" --country IN --target 50

# General pet search
python tiktok_channel_finder.py --keywords "animals, pets, cute" --target 100
```

## Dependencies

Both tools automatically check for required dependencies:
- **Video Processor**: `yt-dlp`, `google-genai`, `python-dotenv`
- **Channel Finder**: `openai`, `csv` (built-in)

## Files

- `video_processor.py` - Main video download and AI analysis tool
- `tiktok_channel_finder.py` - TikTok channel discovery tool  
- `requirements.txt` - Python dependencies
- `pet_channels.csv` - Channel database (auto-generated)
- `metadata.json` - Video analysis results (auto-generated)
- `downloads/` - Downloaded video files (auto-generated)