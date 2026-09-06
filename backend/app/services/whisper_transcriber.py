import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class WhisperTranscriber:
    """Whisper Speech-to-Text service."""
    
    def __init__(self, model_size: str = 'base'):
        self.available = False
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
            self.available = True
            logger.info(f"Faster-whisper model ({model_size}) loaded successfully.")
        except ImportError:
            logger.warning("faster-whisper not installed. Falling back to stub mode.")
            self.model = None

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: path to the audio file
            
        Returns:
            Dictionary with transcript text and metadata
        """
        if not self.available:
            return {
                "text": "This is a placeholder transcript. Please install faster-whisper to enable transcription.",
                "segments": [],
                "language": "en"
            }
            
        try:
            segments, info = self.model.transcribe(audio_path, beam_size=5)
            
            text = ""
            segments_list = []
            
            for segment in segments:
                text += segment.text + " "
                segments_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                })
                
            return {
                "text": text.strip(),
                "segments": segments_list,
                "language": info.language
            }
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return {
                "text": "",
                "segments": [],
                "language": "unknown"
            }
