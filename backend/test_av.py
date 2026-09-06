
import av
import numpy as np

def decode_audio_av(file_path, target_sr=16000):
    container = av.open(file_path)
    stream = container.streams.audio[0]
    # Resampler to target_sr and mono
    resampler = av.AudioResampler(
        format='flt', # Float32
        layout='mono',
        rate=target_sr,
    )
    
    audio_data = []
    for frame in container.decode(stream):
        frame.pts = None # Required for some webm files
        resampled_frames = resampler.resample(frame)
        for resampled_frame in resampled_frames:
            arr = resampled_frame.to_ndarray()
            audio_data.append(arr)
            
    # Flush resampler
    for resampled_frame in resampler.resample(None):
        arr = resampled_frame.to_ndarray()
        audio_data.append(arr)
        
    y = np.concatenate(audio_data, axis=1).squeeze()
    
    # Normalize
    if np.max(np.abs(y)) > 0:
        y = y / np.max(np.abs(y))
        
    return y, target_sr

