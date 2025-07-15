# Video Downloader with AI Description

A Python script that downloads videos from TikTok and Instagram, extracts the first frame, and generates AI-powered descriptions using OpenAI's GPT-4.

## Features

- Download videos from TikTok and Instagram URLs
- Extract first frame as PNG image
- Generate AI descriptions of video content
- Process multiple links from a file
- Save metadata in JSON format

## Requirements

- Python 3.7+
- yt-dlp
- ffmpeg
- OpenAI API key

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install system dependencies:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

3. Create `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Add video URLs to `links.txt` (one per line)
2. Run the script:
```bash
python video_processor.py
```

## Output

- **Videos**: Downloaded to `downloads/` folder
- **Frames**: Extracted to `frames/` folder  
- **Metadata**: Saved to `metadata.json` with video info and AI descriptions

## Example

```bash
# Add links to links.txt
echo "https://www.instagram.com/reels/example/" >> links.txt
echo "https://www.tiktok.com/@user/video/123456789" >> links.txt

# Process videos
python video_processor.py
```

## License

MIT License