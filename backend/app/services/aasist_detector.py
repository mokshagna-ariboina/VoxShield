import json
import logging
import os
import torch
import numpy as np
import soundfile as sf
import librosa
from typing import Dict, Any

from aasist.models.AASIST import Model

logger = logging.getLogger(__name__)

# Official AASIST padding: tile-repeat the signal (no zero-padding).
# Matches data_utils.py pad() from clovaai/aasist.
def _tile_pad(x: np.ndarray, max_len: int = 64600) -> np.ndarray:
    x_len = x.shape[0]
    if x_len >= max_len:
        return x[:max_len]
    num_repeats = int(max_len / x_len) + 1
    padded_x = np.tile(x, (1, num_repeats))[:, :max_len][0]
    return padded_x


class AASISTDetector:
    """AASIST model inference service for audio anti-spoofing."""
    
    def __init__(self, config_path: str, checkpoint_path: str, device: str = 'cpu'):
        self.device = torch.device(device)
        self.model_loaded = False
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            d_args = config.get("model_config", {})
            
            self.model = Model(d_args).to(self.device)
            
            if os.path.exists(checkpoint_path):
                self.model.load_state_dict(torch.load(checkpoint_path, map_location=self.device))
                self.model.eval()
                self.model_loaded = True
                logger.info("AASIST model loaded successfully.")
            else:
                logger.warning(f"Checkpoint not found at {checkpoint_path}. Running in dummy mode.")
                
        except Exception as e:
            logger.error(f"Error loading AASIST model: {e}")

    def detect_file(self, file_path: str) -> Dict[str, Any]:
        """
        Run inference using the official AASIST preprocessing pipeline:
        1. Load audio at 16 kHz mono (no amplitude normalization).
        2. Tile-pad (repeat) short clips to 64600 samples.
        3. Feed raw float waveform to the model.

        Class convention (from clovaai/aasist data_utils.py):
            Class 0 = spoof,  Class 1 = bonafide
        """
        target_length = 64600

        if not self.model_loaded:
            return {
                "clone_probability": 0.5,
                "is_clone": False,
                "raw_scores": {"bonafide": 0.5, "spoof": 0.5},
                "error": "Model not loaded"
            }

        # Load audio at 16 kHz mono — NO normalization.
        # We use the robust load_audio which handles m4a, webm, mp3, etc. via PyAV/librosa.
        from app.utils.audio import load_audio
        audio, _ = load_audio(file_path, target_sr=16000, normalize=False)

        # Tile-pad to target length (official method — no zero-padding)
        audio = _tile_pad(audio, target_length)

        tensor_audio = torch.FloatTensor(audio).unsqueeze(0).to(self.device)

        with torch.no_grad():
            _, logits = self.model(tensor_audio)
            probs = torch.nn.functional.softmax(logits, dim=1).cpu().numpy()[0]

        # Class 0 = spoof, Class 1 = bonafide
        spoof_prob = float(probs[0])
        bonafide_prob = float(probs[1])

        return {
            "clone_probability": spoof_prob,
            "is_clone": spoof_prob > 0.5,
            "raw_scores": {
                "bonafide": bonafide_prob,
                "spoof": spoof_prob
            }
        }

    def detect(self, audio: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
        """
        Legacy interface — kept for backward compatibility.
        Accepts pre-loaded audio. Applies tile-pad and correct class mapping
        but cannot undo normalization done by the caller.
        Prefer detect_file() for accurate results.
        """
        target_length = 64600

        if not self.model_loaded:
            return {
                "clone_probability": 0.5,
                "is_clone": False,
                "raw_scores": {"bonafide": 0.5, "spoof": 0.5},
                "error": "Model not loaded"
            }

        # Tile-pad (official method)
        audio = _tile_pad(audio, target_length)

        tensor_audio = torch.FloatTensor(audio).unsqueeze(0).to(self.device)

        with torch.no_grad():
            _, logits = self.model(tensor_audio)
            probs = torch.nn.functional.softmax(logits, dim=1).cpu().numpy()[0]

        # Class 0 = spoof, Class 1 = bonafide
        spoof_prob = float(probs[0])
        bonafide_prob = float(probs[1])

        return {
            "clone_probability": spoof_prob,
            "is_clone": spoof_prob > 0.5,
            "raw_scores": {
                "bonafide": bonafide_prob,
                "spoof": spoof_prob
            }
        }
