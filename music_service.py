# backend/music_service.py
import os
import io
import time
import requests
from typing import Tuple, Optional

# --- Spotify curated track fetch (Client Credentials flow) ---
# uses spotipy for convenience
try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    SPOTIPY_AVAILABLE = True
except Exception:
    SPOTIPY_AVAILABLE = False

# --- MusicGen / Audiocraft (optional heavy generation) ---
try:
    from audiocraft.models import MusicGen
    from audiocraft.data.audio import audio_write
    import torch
    MUSICGEN_AVAILABLE = True
except Exception:
    MUSICGEN_AVAILABLE = False

# helper: Spotify client
def _spotify_client():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not (client_id and client_secret):
        raise RuntimeError("Spotify credentials not set (SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET)")
    return spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

# curated mapping emotion -> search query (tweakable)
CURATED_QUERIES = {
    "happy": "happy upbeat pop",
    "sad": "acoustic sad mellow",
    "calm": "ambient calm relaxation",
    "angry": "intense aggressive rock",
    "fearful": "dark cinematic ambient",
    "neutral": "chill instrumental",
    "surprised": "energetic electronic",
    "disgust": "detached experimental"
}

def fetch_spotify_preview_for_emotion(emotion: str) -> Tuple[Optional[str], Optional[bytes]]:
    """
    Return (preview_url, None) if preview URL available,
    or (None, bytes) if we download the preview bytes.
    """
    if not SPOTIPY_AVAILABLE:
        raise RuntimeError("spotipy not installed")
    sp = _spotify_client()
    q = CURATED_QUERIES.get(emotion, CURATED_QUERIES["neutral"])
    # search top tracks
    res = sp.search(q, type="track", limit=10)
    tracks = res.get("tracks", {}).get("items", [])
    # prefer tracks that have preview_url
    for t in tracks:
        preview = t.get("preview_url")
        if preview:
            # return direct preview URL (30s mp3)
            return preview, None
    # fallback: try first track and try to fetch external_url -> None
    if tracks:
        # fallback to full Spotify track url
        return tracks[0].get("external_urls", {}).get("spotify"), None
    return None, None

# MusicGen generation (if available)
def generate_music_with_musicgen(prompt: str, duration_s: int = 8) -> bytes:
    """
    Generate a short audio snippet (WAV) for given prompt using MusicGen (audiocraft).
    Returns WAV bytes (16-bit PCM) or raises if unavailable.
    NOTE: requires MUSICGEN_AVAILABLE and device with memory (GPU recommended).
    """
    if not MUSICGEN_AVAILABLE:
        raise RuntimeError("MusicGen not available on server. Install audiocraft and dependencies.")
    # load model (small by default). Cache model globally if repeated calls are expected.
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = MusicGen.get_pretrained('melody')  # or 'small' / 'medium' depending on version
    model.to(device)
    model.set_generation_params(duration=duration_s)
    # generate with prompt list
    wav = model.generate([prompt], progress=True)[0]  # returns numpy array (samples,)
    # write to bytes buffer as WAV using scipy or soundfile
    import soundfile as sf
    bio = io.BytesIO()
    sf.write(bio, wav, samplerate=32000, format="WAV")
    bio.seek(0)
    return bio.read()

# Single unified function used by router
def get_music_for_emotion(emotion: str, mode: str = "curated", duration: int = 8):
    """
    mode: 'curated' -> spotify preview; 'generated' -> MusicGen; 'auto' -> try generated else curated
    Returns a dict: {"type":"url"|"bytes", "content": <url or bytes>, "meta": {...}}
    """
    emotion = (emotion or "neutral").lower()
    mode = mode or "auto"
    if mode == "generated":
        try:
            prompt = f"A short instrumental soundtrack evoking {emotion} mood, cinematic and {CURATED_QUERIES.get(emotion,'')}"
            audio_bytes = generate_music_with_musicgen(prompt, duration_s=duration)
            return {"type":"bytes", "content": audio_bytes, "meta": {"source":"musicgen", "prompt": prompt}}
        except Exception as e:
            # bubble up or fallback
            return {"type":"error", "message": str(e)}
    # curated fallback (spotify)
    try:
        preview_url, _ = fetch_spotify_preview_for_emotion(emotion)
        if preview_url:
            return {"type":"url", "content": preview_url, "meta": {"source":"spotify_preview"}}
        return {"type":"error", "message":"No preview found"}
    except Exception as e:
        return {"type":"error", "message": str(e)}
