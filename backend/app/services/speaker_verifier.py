import logging
import numpy as np
import pickle
import torch
import torchaudio
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SpeakerVerifier:
    """Speaker verification service using SpeechBrain."""
    
    def __init__(self):
        self.available = False
        try:
            from speechbrain.inference.classifiers import EncoderClassifier
            # Load ECAPA-TDNN model
            self.classifier = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb")
            self.available = True
            logger.info("SpeechBrain initialized successfully.")
        except ImportError:
            logger.warning("speechbrain not installed. Speaker verification disabled.")
        except Exception as e:
            logger.warning(f"Failed to initialize SpeechBrain: {e}")

    def extract_embedding(self, audio_path: str) -> Optional[np.ndarray]:
        """
        Extract speaker embedding vector.
        """
        if not self.available:
            return None
            
        try:
            from app.utils.audio import load_audio
            import torchaudio.transforms as T
            
            # Load audio using the app's robust fallback loader
            audio_data, sr = load_audio(audio_path, normalize=True)
            signal = torch.tensor(audio_data, dtype=torch.float32)
            
            # Resample to 16kHz if needed (ECAPA-TDNN standard)
            if sr != 16000:
                resampler = T.Resample(sr, 16000, dtype=torch.float32)
                signal = resampler(signal.unsqueeze(0)).squeeze(0)
                
            # Add batch dimension
            signal = signal.unsqueeze(0)
            
            # extract embeddings
            embeddings = self.classifier.encode_batch(signal)
            
            # embeddings shape is [batch, 1, dims] -> squeeze
            emb = embeddings.squeeze().detach().cpu().numpy()
            return emb
        except Exception as e:
            logger.error(f"Error extracting embedding: {e}")
            return None

    def compare(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        """
        if embedding1 is None or embedding2 is None:
            return 0.0
            
        dot_product = np.dot(embedding1, embedding2)
        norm_a = np.linalg.norm(embedding1)
        norm_b = np.linalg.norm(embedding2)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return float(dot_product / (norm_a * norm_b))

    def verify(self, audio_path: str, enrolled_embedding: bytes) -> Dict[str, Any]:
        """
        Verify an audio sample against an enrolled embedding.
        
        Args:
            audio_path: path to audio file
            enrolled_embedding: pickled numpy array of enrolled embedding
            
        Returns:
            Dictionary with match results
        """
        if not self.available:
            return {
                "match": False,
                "similarity_score": 0.0,
                "available": False
            }
            
        try:
            enrolled_np = pickle.loads(enrolled_embedding)
            new_embedding = self.extract_embedding(audio_path)
            
            if new_embedding is None:
                return {
                    "match": False,
                    "similarity_score": 0.0,
                    "available": True
                }
                
            sim_score = self.compare(enrolled_np, new_embedding)
            
            return {
                "match": sim_score > 0.7,
                "similarity_score": sim_score,
                "available": True
            }
        except Exception as e:
            logger.error(f"Error during verification: {e}")
            return {
                "match": False,
                "similarity_score": 0.0,
                "available": True
            }
