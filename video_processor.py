#!/usr/bin/env python3
import os
import sys
import subprocess
import json
import base64
from pathlib import Path
from typing import List, Dict, Any
import re

def load_links_from_file(file_path: str) -> List[str]:
    """Load video URLs from a text file"""
    if not os.path.exists(file_path):
        print(f"Links file not found: {file_path}")
        return []
    
    with open(file_path, 'r') as f:
        links = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    return links

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove invalid characters"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'[#@]', '', filename)
    filename = filename.replace('...', '')
    if len(filename) > 100:
        filename = filename[:100]
    return filename.strip()

def download_video_with_ytdlp(url: str, output_dir: str = "downloads") -> Dict[str, Any]:
    """Download video using yt-dlp command"""
    Path(output_dir).mkdir(exist_ok=True)
    
    try:
        # Get video info first
        info_cmd = ['yt-dlp', '--dump-json', url]
        info_result = subprocess.run(info_cmd, capture_output=True, text=True)
        
        if info_result.returncode != 0:
            return {'success': False, 'error': f'Failed to get video info: {info_result.stderr}'}
        
        info = json.loads(info_result.stdout)
        title = info.get('title', 'Unknown')
        
        # Download video
        download_cmd = ['yt-dlp', url, '-o', f'{output_dir}/%(title)s.%(ext)s']
        download_result = subprocess.run(download_cmd, capture_output=True, text=True)
        
        if download_result.returncode != 0:
            return {'success': False, 'error': f'Download failed: {download_result.stderr}'}
        
        # Find downloaded file
        sanitized_title = sanitize_filename(title)
        video_files = list(Path(output_dir).glob(f"*{sanitized_title}*"))
        
        if not video_files:
            # Try to find the most recent file
            video_files = [f for f in Path(output_dir).iterdir() if f.is_file() and f.suffix in ['.mp4', '.mkv', '.webm']]
            if video_files:
                video_files = sorted(video_files, key=lambda x: x.stat().st_mtime, reverse=True)
        
        if video_files:
            video_path = str(video_files[0])
            print(f"✅ Downloaded: {os.path.basename(video_path)}")
            
            return {
                'success': True,
                'video_path': video_path,
                'title': title,
                'url': url,
                'uploader': info.get('uploader', 'Unknown'),
                'duration': info.get('duration', 0)
            }
        else:
            return {'success': False, 'error': 'Downloaded file not found'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def extract_first_frame(video_path: str, output_dir: str = "frames") -> str:
    """Extract first frame from video as PNG"""
    try:
        Path(output_dir).mkdir(exist_ok=True)
        
        video_name = Path(video_path).stem
        frame_path = os.path.join(output_dir, f"{sanitize_filename(video_name)}_frame.png")
        
        cmd = [
            'ffmpeg', '-i', video_path, 
            '-vframes', '1', 
            '-q:v', '2',
            '-y',
            frame_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(frame_path):
            print(f"✅ Frame extracted: {os.path.basename(frame_path)}")
            return frame_path
        else:
            print(f"❌ Frame extraction failed: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error extracting frame: {str(e)}")
        return None

def get_image_description(image_path: str) -> str:
    """Get image description from OpenAI API"""
    try:
        from openai import OpenAI
        from dotenv import load_dotenv
        
        load_dotenv()
        
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        with open(image_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe this video frame in 1-2 sentences. Focus on the main subject, action, and overall scene. Be concise and descriptive."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        description = response.choices[0].message.content
        print(f"✅ Generated description: {description[:50]}...")
        return description
        
    except Exception as e:
        print(f"❌ Error getting image description: {str(e)}")
        return "Description not available"

def save_metadata(metadata_list: List[Dict], output_file: str = "metadata.json"):
    """Save metadata to JSON file"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_list, f, indent=2, ensure_ascii=False)
        print(f"✅ Metadata saved to {output_file}")
    except Exception as e:
        print(f"❌ Error saving metadata: {str(e)}")

def process_links(links_file: str = "links.txt", output_dir: str = "downloads"):
    """Process all links from file"""
    links = load_links_from_file(links_file)
    
    if not links:
        print("No links found to process")
        return
    
    print(f"Found {len(links)} links to process")
    metadata_list = []
    
    for i, url in enumerate(links, 1):
        print(f"\n[{i}/{len(links)}] Processing: {url}")
        
        # Download video
        download_result = download_video_with_ytdlp(url, output_dir)
        
        if download_result['success']:
            video_path = download_result['video_path']
            
            # Extract first frame
            frame_path = extract_first_frame(video_path, "frames")
            
            # Get description if frame was extracted
            description = ""
            if frame_path:
                description = get_image_description(frame_path)
            
            # Create metadata entry
            metadata = {
                'video_name': os.path.basename(video_path),
                'video_title': download_result['title'],
                'video_url': url,
                'image_name': os.path.basename(frame_path) if frame_path else None,
                'description': description,
                'uploader': download_result.get('uploader', 'Unknown'),
                'duration': download_result.get('duration', 0)
            }
            
            metadata_list.append(metadata)
            
        else:
            print(f"❌ Failed to download: {download_result.get('error', 'Unknown error')}")
    
    # Save all metadata
    save_metadata(metadata_list)
    print(f"\n✅ Processing complete! Processed {len(metadata_list)} videos successfully.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Process video links with AI description')
    parser.add_argument('--links-file', '-l', default='links.txt', help='File containing video URLs')
    parser.add_argument('--output-dir', '-o', default='downloads', help='Output directory for videos')
    
    args = parser.parse_args()
    
    # Check dependencies
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ yt-dlp not found. Please install it first.")
        sys.exit(1)
    
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found. Please install FFmpeg.")
        sys.exit(1)
    
    process_links(args.links_file, args.output_dir)