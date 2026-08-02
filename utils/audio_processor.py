import yt_dlp
from pydub import AudioSegment
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi

DOWNLOAD_DIR = 'downloades'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def extract_youtube_video_id(url: str) -> str:
    pattern = r'(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_youtube_transcript_text(url: str) -> str:
    """Attempt direct transcript extraction from YouTube."""
    video_id = extract_youtube_video_id(url)
    if not video_id:
        return None
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        text = " ".join([t['text'] for t in transcript if t.get('text')])
        if len(text.strip()) > 30:
            print(f"Successfully fetched YouTube direct transcript ({len(text.split())} words).")
            return text
    except Exception as e:
        print(f"Direct YouTube transcript API failed: {e}")
    return None

def download_with_pytubefix(url: str) -> str:
    """Download audio using pytubefix to bypass 403 Forbidden cloud IP blocks."""
    from pytubefix import YouTube
    yt = YouTube(url)
    stream = yt.streams.filter(only_audio=True).first()
    out_file = stream.download(output_path=DOWNLOAD_DIR)
    base, _ = os.path.splitext(out_file)
    wav_file = base + ".wav"
    audio = AudioSegment.from_file(out_file)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(wav_file, format="wav")
    if os.path.exists(out_file) and out_file != wav_file:
        try:
            os.remove(out_file)
        except Exception:
            pass
    return wav_file

def download_youtube_audio(url: str) -> str:
    # Try pytubefix first (bypasses datacenter 403 blocks)
    try:
        print("Attempting audio download with pytubefix...")
        return download_with_pytubefix(url)
    except Exception as pe:
        print(f"pytubefix download failed ({pe}). Trying yt-dlp with cookies...")

    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    
    # Check for cookies.txt in root or downloades dir or env
    root_cookies = "cookies.txt"
    dir_cookies = os.path.join(DOWNLOAD_DIR, "cookies.txt")
    cookies_content = os.getenv("YOUTUBE_COOKIES")
    
    if cookies_content:
        with open(dir_cookies, "w") as f:
            f.write(cookies_content)
        cookiefile_to_use = dir_cookies
    elif os.path.exists(root_cookies):
        cookiefile_to_use = root_cookies
    elif os.path.exists(dir_cookies):
        cookiefile_to_use = dir_cookies
    else:
        cookiefile_to_use = None

    ydl_opts = {
        "format": "ba/ba*/bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "nocheckcertificate": True,
        "no_color": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        },
        "extractor_args": {
            "youtube": {
                "player_client": ["web", "android"]
            }
        }
    }

    if cookiefile_to_use:
        ydl_opts["cookiefile"] = cookiefile_to_use

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        raw_filename = ydl.prepare_filename(info)
        base_path = os.path.splitext(raw_filename)[0]
        wav_filename = base_path + ".wav"
        if os.path.exists(wav_filename):
            return wav_filename
        return raw_filename


def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000) #16khz
    audio.export(output_path, format="wav")
    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000 

    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start : start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")

        chunks.append(chunk_path)
    
    return chunks

def process_input(source: str) -> tuple:
    """
    Returns (result_data, is_direct_transcript).
    If is_direct_transcript is True, result_data is the full transcript string.
    If is_direct_transcript is False, result_data is a list of chunk file paths.
    """
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Attempting direct transcript extraction...")
        direct_text = get_youtube_transcript_text(source)
        if direct_text:
            return (direct_text, True)

        print("Direct transcript unavailable. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return (chunks, False)
