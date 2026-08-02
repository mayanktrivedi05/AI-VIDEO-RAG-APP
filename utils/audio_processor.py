from pydub import AudioSegment
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi

DOWNLOAD_DIR = 'downloades'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
<<<<<<< HEAD

def extract_youtube_video_id(url: str) -> str:
    pattern = r'(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_youtube_transcript_text(url: str) -> str:
    """Attempt direct transcript extraction from YouTube in 1s (0% 403 error)."""
    video_id = extract_youtube_video_id(url)
    if not video_id:
        return None
    
    transcript = None
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        # Try fetching preferred languages first (hi, en, en-IN)
        try:
            transcript = transcript_list.find_transcript(['hi', 'en', 'en-IN']).fetch()
        except Exception:
            # Fall back to the first available transcript in any language
            for t in transcript_list:
                transcript = t.fetch()
                break
    except Exception as e:
        print(f"Transcript list fetch failed: {e}")
        try:
            if hasattr(YouTubeTranscriptApi, 'get_transcript'):
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
        except Exception as e2:
            print(f"Direct YouTube transcript API failed: {e2}")

    if transcript:
        words = []
        for snippet in transcript:
            if hasattr(snippet, 'text'):
                words.append(snippet.text)
            elif isinstance(snippet, dict) and 'text' in snippet:
                words.append(snippet['text'])
        
        full_text = " ".join(words)
        if len(full_text.strip()) > 30:
            print(f"Successfully fetched YouTube direct transcript ({len(full_text.split())} words).")
            return full_text

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
        print(f"pytubefix download failed ({pe}). Trying yt-dlp...")

    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    
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

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        raw_filename = ydl.prepare_filename(info)
        base_path = os.path.splitext(raw_filename)[0]
        wav_filename = base_path + ".wav"
        if os.path.exists(wav_filename):
            return wav_filename
        return raw_filename

=======
>>>>>>> b9bdd01 (Revert all YouTube URL setup and simplify app to direct file upload & local file path)

def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000) # 16kHz mono
    audio.export(output_path, format="wav")
    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000 

    chunks = []
<<<<<<< HEAD

=======
>>>>>>> b9bdd01 (Revert all YouTube URL setup and simplify app to direct file upload & local file path)
    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start : start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")
<<<<<<< HEAD

=======
>>>>>>> b9bdd01 (Revert all YouTube URL setup and simplify app to direct file upload & local file path)
        chunks.append(chunk_path)
    
    return chunks

<<<<<<< HEAD
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
=======
def process_input(source: str) -> list:
    """Process video/audio file path and return audio chunk file paths."""
    print("Converting file to WAV...")
    wav_path = convert_to_wav(source)
>>>>>>> b9bdd01 (Revert all YouTube URL setup and simplify app to direct file upload & local file path)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
<<<<<<< HEAD
    return (chunks, False)
=======
    return chunks
>>>>>>> b9bdd01 (Revert all YouTube URL setup and simplify app to direct file upload & local file path)
