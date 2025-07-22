#!/usr/bin/env python3
"""
Video Processor with AI Analysis

A tool for downloading videos and analyzing them using Google AI Studio (Gemini).
Supports both single video processing and batch processing from a links file.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any
import re


def load_links_from_file(file_path: str) -> List[str]:
    """Load video URLs from a text file"""
    if not os.path.exists(file_path):
        print(f"Links file not found: {file_path}")
        return []

    with open(file_path, "r") as f:
        links = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]

    return links


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove invalid characters"""
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    filename = re.sub(r"[#@]", "", filename)
    filename = filename.replace("...", "")
    if len(filename) > 100:
        filename = filename[:100]
    return filename.strip()


def download_video_with_ytdlp(
    url: str, output_dir: str = "downloads"
) -> Dict[str, Any]:
    """Download video using yt-dlp command"""
    Path(output_dir).mkdir(exist_ok=True)

    try:
        # Get video info first
        info_cmd = ["yt-dlp", "--dump-json", url]
        info_result = subprocess.run(info_cmd, capture_output=True, text=True)

        if info_result.returncode != 0:
            return {
                "success": False,
                "error": f"Failed to get video info: {info_result.stderr}",
            }

        info = json.loads(info_result.stdout)
        title = info.get("title", "Unknown")

        # Download video
        download_cmd = ["yt-dlp", url, "-o", f"{output_dir}/%(title)s.%(ext)s"]
        download_result = subprocess.run(download_cmd, capture_output=True, text=True)

        if download_result.returncode != 0:
            return {
                "success": False,
                "error": f"Download failed: {download_result.stderr}",
            }

        # Find downloaded file
        sanitized_title = sanitize_filename(title)
        video_files = list(Path(output_dir).glob(f"*{sanitized_title}*"))

        if not video_files:
            # Try to find the most recent file
            video_files = [
                f
                for f in Path(output_dir).iterdir()
                if f.is_file() and f.suffix in [".mp4", ".mkv", ".webm"]
            ]
            if video_files:
                video_files = sorted(
                    video_files, key=lambda x: x.stat().st_mtime, reverse=True
                )

        if video_files:
            video_path = str(video_files[0])
            print(f"✅ Downloaded: {os.path.basename(video_path)}")

            return {
                "success": True,
                "video_path": video_path,
                "title": title,
                "url": url,
                "uploader": info.get("uploader", "Unknown"),
                "duration": info.get("duration", 0),
            }
        else:
            return {"success": False, "error": "Downloaded file not found"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def analyze_video_with_gemini(video_path: str) -> Dict[str, Any]:
    """Analyze video using Google AI Studio Gemini API"""
    try:
        from google import genai
        from google.genai import types
        from dotenv import load_dotenv

        load_dotenv()

        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        # Read video file as binary data
        with open(video_path, "rb") as video_file:
            video_data = video_file.read()

        model = "gemini-2.5-pro"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(
                        mime_type="video/mp4",
                        data=video_data,
                    ),
                    types.Part.from_text(
                        text="""Analyze this short-form video frame by frame and identify distinct scenes or segments. Provide a comprehensive description in JSON format, breaking down each scene with timestamps and descriptions.

Respond ONLY with valid JSON in the following structure:

{
  "video_summary": "Brief 1-2 sentence overview of the entire video",
  "total_duration": "Total video length in seconds",
  "content_type": "Type of content (dance, comedy, tutorial, lifestyle, food, etc.)",
  "overall_mood": "Overall emotional tone or vibe",
  "scenes": [
    {
      "scene_number": 1,
      "start_timestamp": "0:00",
      "duration": "3.5s",
      "description": "Detailed description of what's happening in this scene",
      "text_overlay": "Any visible text, captions, or graphics in this scene",
      "main_action": "Primary action or focus of this scene",
      "visual_elements": "Key visual elements, colors, lighting for this scene"
    }
  ],
  "audio_elements": {
    "music_type": "Background music description",
    "voice_over": true,
    "sound_effects": "Notable audio elements"
  },
  "visual_style": {
    "camera_work": "Overall camera movements and style",
    "setting": "Location/environment",
    "production_quality": "Low/Medium/High"
  },
  "engagement_elements": ["hooks", "transitions", "calls to action"],
  "suggested_tags": ["relevant", "hashtags", "keywords"],
  "platform_indicators": "TikTok/YouTube/Instagram visual cues or watermarks"
}

IMPORTANT INSTRUCTIONS:
- Identify scene changes based on: cuts, transitions, significant action changes, or text overlay changes
- For each scene, provide accurate timestamp (format: "M:SS" or "SS.S")
- If no text overlay exists in a scene, use "none" for text_overlay field
- Be precise with scene durations and ensure they add up to total video length
- Include ALL visible text overlays, even brief ones
- Your response must be valid JSON only with no additional text

DO NOT include any text outside the JSON structure."""
                    ),
                ],
            ),
        ]

        generate_content_config = types.GenerateContentConfig(
            media_resolution="MEDIA_RESOLUTION_UNSPECIFIED",
            response_mime_type="application/json",
        )

        response_text = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            response_text += chunk.text

        # Parse JSON response
        analysis = json.loads(response_text)
        print(f"✅ Generated video analysis: {analysis.get('description', '')[:50]}...")
        return analysis

    except Exception as e:
        print(f"❌ Error analyzing video: {str(e)}")
        return {
            "video_summary": "Analysis not available",
            "total_duration": "unknown",
            "content_type": "unknown",
            "overall_mood": "unknown",
            "scenes": [],
            "audio_elements": {
                "music_type": "unknown",
                "voice_over": False,
                "sound_effects": "unknown",
            },
            "visual_style": {
                "camera_work": "unknown",
                "setting": "unknown",
                "production_quality": "unknown",
            },
            "engagement_elements": [],
            "suggested_tags": [],
            "platform_indicators": "unknown",
        }


def save_metadata(metadata_list: List[Dict], output_file: str = "metadata.json"):
    """Save metadata to JSON file"""
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(metadata_list, f, indent=2, ensure_ascii=False)
        print(f"✅ Metadata saved to {output_file}")
    except Exception as e:
        print(f"❌ Error saving metadata: {str(e)}")


def process_single_link(url: str, output_dir: str = "downloads"):
    """Process a single video link"""
    print(f"Processing single link: {url}")

    # Download video
    download_result = download_video_with_ytdlp(url, output_dir)

    if download_result["success"]:
        video_path = download_result["video_path"]

        # Analyze video with Gemini
        video_analysis = analyze_video_with_gemini(video_path)

        # Create metadata entry
        metadata = {
            "video_name": os.path.basename(video_path),
            "video_title": download_result["title"],
            "video_url": url,
            "uploader": download_result.get("uploader", "Unknown"),
            "duration": download_result.get("duration", 0),
            "analysis": video_analysis,
        }

        # Save metadata for single video
        save_metadata([metadata], "single_video_metadata.json")
        print(f"\n✅ Single video processing complete!")
        return metadata
    else:
        print(f"❌ Failed to download: {download_result.get('error', 'Unknown error')}")
        return None


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

        if download_result["success"]:
            video_path = download_result["video_path"]

            # Analyze video with Gemini
            video_analysis = analyze_video_with_gemini(video_path)

            # Create metadata entry
            metadata = {
                "video_name": os.path.basename(video_path),
                "video_title": download_result["title"],
                "video_url": url,
                "uploader": download_result.get("uploader", "Unknown"),
                "duration": download_result.get("duration", 0),
                "analysis": video_analysis,
            }

            metadata_list.append(metadata)

        else:
            print(
                f"❌ Failed to download: {download_result.get('error', 'Unknown error')}"
            )

    # Save all metadata
    save_metadata(metadata_list)
    print(
        f"\n✅ Processing complete! Processed {len(metadata_list)} videos successfully."
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Process video links with AI description"
    )
    parser.add_argument(
        "--links-file", "-l", default="links.txt", help="File containing video URLs"
    )
    parser.add_argument(
        "--output-dir", "-o", default="downloads", help="Output directory for videos"
    )
    parser.add_argument(
        "--single-link", "-s", help="Process a single video URL instead of links file"
    )

    args = parser.parse_args()

    # Check dependencies
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ yt-dlp not found. Please install it first.")
        sys.exit(1)

    # Check for google-genai package
    try:
        import google.genai
    except ImportError:
        print("❌ google-genai not found. Please install it: pip install google-genai")
        sys.exit(1)

    # Process single link or links file
    if args.single_link:
        process_single_link(args.single_link, args.output_dir)
    else:
        process_links(args.links_file, args.output_dir)
