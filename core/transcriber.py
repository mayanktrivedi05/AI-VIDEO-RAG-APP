import whisper
import os
import requests
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor

# Sarvam's sync STT-translate API rejects audio longer than 30s.
# We slice each chunk into 25s pieces (with a 5s safety margin) before sending.
SARVAM_PIECE_SECONDS = 25

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

def transcribe_chunk_whisper(chunk_path: str) -> str:
    """Transcribe an audio chunk using OpenAI Whisper (local CPU execution)."""
    print(f"Loading Whisper model '{WHISPER_MODEL}'...")
    model = whisper.load_model(WHISPER_MODEL)

    print(f"Transcribing {chunk_path} with Whisper...")
    result = model.transcribe(chunk_path)
    return result["text"]


def _send_to_sarvam(piece_path: str) -> str:
    """Helper to send a single <=30s audio file to Sarvam AI API."""
    url = "https://api.sarvam.ai/speech-to-text-translate"
    headers = {"api-subscription-key": SARVAM_API_KEY}

    with open(piece_path, "rb") as f:
        files = {"file": (os.path.basename(piece_path), f, "audio/wav")}
        data = {"model": "saaras:v2.5"}
        response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code != 200:
        raise RuntimeError(
            f"Sarvam API error ({response.status_code}): {response.text}"
        )

    return response.json().get("transcript", "")


def transcribe_chunk_sarvam(chunk_path: str) -> str:
    """
    Sarvam sync API only accepts <=30s audio. We split this chunk into
    25-second pieces, send each in parallel, and join the transcripts.
    """
    if not SARVAM_API_KEY:
        raise RuntimeError("SARVAM_API_KEY is not set in environment / .env")

    audio = AudioSegment.from_wav(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000

    total_pieces = (len(audio) + piece_ms - 1) // piece_ms
    piece_paths = []

    for i, start in enumerate(range(0, len(audio), piece_ms)):
        piece = audio[start: start + piece_ms]
        piece_path = f"{chunk_path}_piece_{i}.wav"
        piece.export(piece_path, format="wav")
        piece_paths.append((i, piece_path))

    def process_piece(item):
        idx, piece_path = item
        try:
            print(f"  → Sarvam piece {idx + 1}/{total_pieces} ...")
            return idx, _send_to_sarvam(piece_path)
        finally:
            if os.path.exists(piece_path):
                os.remove(piece_path)

    results = [None] * len(piece_paths)
    with ThreadPoolExecutor(max_workers=6) as executor:
        for idx, text in executor.map(process_piece, piece_paths):
            results[idx] = text

    return " ".join([r for r in results if r]).strip()


def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    """Route transcription request to appropriate engine based on language."""
    if language.lower() == "hinglish":
        print("Language set to Hinglish — using Sarvam AI (saaras:v2.5)...")
        return transcribe_chunk_sarvam(chunk_path)
    else:
        print("Language set to English — using Whisper (base)...")
        return transcribe_chunk_whisper(chunk_path)


def transcribe_all(chunks: list, language: str = "english") -> str:
    """Transcribe a list of audio chunk file paths and return combined text."""
    full_transcript = ""

    for i, chunk_path in enumerate(chunks):
        print(f"\nProcessing chunk {i+1}/{len(chunks)}: {chunk_path}")
        text = transcribe_chunk(chunk_path, language)
        full_transcript += f" {text}"

    print("Transcription complete.")
    return full_transcript.strip()