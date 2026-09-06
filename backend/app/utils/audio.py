import os
import uuid
from typing import Tuple
from fastapi import UploadFile
import numpy as np
import librosa
import aiofiles
import av

def load_audio(file_path: str, target_sr: int = 16000, normalize: bool = True) -> Tuple[np.ndarray, int]:
    """
    Load any audio format, resample to target_sr, convert to mono, and optionally normalize.
    """
    try:
        # First try librosa (works well for wav, mp3, flac if soundfile supports it)
        # It's faster for WAV files.
        y, sr = librosa.load(file_path, sr=target_sr, mono=True)
    except Exception:
        # Fallback to PyAV for formats like webm/opus which soundfile rejects
        container = av.open(file_path)
        stream = container.streams.audio[0]
        resampler = av.AudioResampler(format='flt', layout='mono', rate=target_sr)
        
        audio_data = []
        for frame in container.decode(stream):
            frame.pts = None
            resampled_frames = resampler.resample(frame)
            for r_frame in resampled_frames:
                audio_data.append(r_frame.to_ndarray())
                
        for r_frame in resampler.resample(None):
            audio_data.append(r_frame.to_ndarray())
            
        y = np.concatenate(audio_data, axis=1).squeeze()
        
    # Normalize audio
    if normalize and np.max(np.abs(y)) > 0:
        y = y / np.max(np.abs(y))
    return y, target_sr

async def save_upload(upload_file: UploadFile, upload_dir: str) -> str:
    """
    Save uploaded file to disk and return the path.
    """
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(upload_file.filename)[1] if upload_file.filename else ".wav"
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(upload_dir, filename)
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await upload_file.read()
        await out_file.write(content)
        
    return file_path
