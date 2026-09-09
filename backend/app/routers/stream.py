from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import uuid
import tempfile
import os
import numpy as np
import scipy.io.wavfile as wavfile
from datetime import datetime
import asyncio

router = APIRouter(prefix="/api/analyze", tags=["stream"])
logger = logging.getLogger(__name__)

# Parameters for the sliding window
SAMPLE_RATE = 16000
BYTES_PER_SAMPLE = 2  # 16-bit
CHANNELS = 1

WINDOW_DURATION_SEC = 3.0
OVERLAP_DURATION_SEC = 1.0

WINDOW_BYTES = int(WINDOW_DURATION_SEC * SAMPLE_RATE * BYTES_PER_SAMPLE * CHANNELS)
OVERLAP_BYTES = int(OVERLAP_DURATION_SEC * SAMPLE_RATE * BYTES_PER_SAMPLE * CHANNELS)

@router.websocket("/stream")
async def analyze_stream(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected for audio stream analysis.")
    
    session_id = str(uuid.uuid4())
    audio_buffer = bytearray()
    chunk_counter = 0
    total_bytes_received = 0

    try:
        while True:
            # Receive raw PCM bytes from Android OkHttp WebSocket
            data = await websocket.receive_bytes()
            chunk_counter += 1
            total_bytes_received += len(data)
            
            logger.info(f"[Stream {session_id}] Received chunk {chunk_counter} ({len(data)} bytes). Cumulative: {total_bytes_received} bytes")
            
            audio_buffer.extend(data)
            
            # If buffer has reached the window size, process it
            if len(audio_buffer) >= WINDOW_BYTES:
                # Extract exactly WINDOW_BYTES
                window_data = audio_buffer[:WINDOW_BYTES]
                
                # Shift buffer by sliding amount
                audio_buffer = audio_buffer[(WINDOW_BYTES - OVERLAP_BYTES):]
                
                # Process the window asynchronously so we don't block the WebSocket receiving loop
                asyncio.create_task(process_audio_window(websocket, session_id, window_data, chunk_counter))

    except WebSocketDisconnect:
        logger.info(f"[Stream {session_id}] WebSocket disconnected. Call ended.")
    except Exception as e:
        logger.error(f"[Stream {session_id}] WebSocket error: {e}")


async def process_audio_window(websocket: WebSocket, session_id: str, window_bytes: bytes, chunk_index: int):
    """Processes a 3-second window of raw PCM audio through the VoxShield pipeline."""
    
    # 1. Decode raw bytes to numpy int16 array
    audio_array = np.frombuffer(window_bytes, dtype=np.int16)
    
    # 2. Save to a temporary WAV file for AASIST/Whisper (they expect file paths)
    fd, temp_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    
    try:
        wavfile.write(temp_path, SAMPLE_RATE, audio_array)
        logger.debug(f"[Stream {session_id}] Processing window (Chunk {chunk_index}, 3.0s)")

        app_state = websocket.app.state
        
        # 3. Run AASIST
        aasist_result = app_state.aasist_detector.detect_file(temp_path)
        clone_probability = aasist_result["clone_probability"]
        
        # 4. Run Whisper
        whisper_result = app_state.whisper_transcriber.transcribe(temp_path)
        transcript = whisper_result["text"].strip()
        
        if not transcript:
            # Silence or unintelligible, skip heavy analysis
            social_risk = 0.0
            composite_risk = clone_probability
            action = "allow"
            decision = "Silence detected"
        else:
            # 5. Social Engineering analysis
            lang_result = app_state.language_analyzer.analyze(transcript)
            social_risk = lang_result["social_engineering_score"]
            
            # 6. Risk Engine Fusion
            # For this live demo event, we leave transaction/speaker mismatch at 0 unless provided
            risk_result = app_state.risk_engine.compute_risk(
                clone_probability=clone_probability,
                social_engineering_score=social_risk,
                speaker_mismatch_score=0.0,
                trust_novelty_score=0.5,
                transaction_risk_score=0.0
            )
            composite_risk = risk_result["composite_risk_score"]
            decision = risk_result["risk_level"]
            action = risk_result["recommended_action"]
            
        # 7. Construct Event Output
        event = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "audio_window_id": chunk_index,
            "transcript_delta": transcript,
            "clone_probability": round(clone_probability, 3),
            "social_risk": round(social_risk if transcript else 0.0, 3),
            "speaker_risk": 0.0,
            "transaction_risk": 0.0,
            "overall_risk": round(composite_risk, 3),
            "decision": decision,
            "recommended_action": action
        }
        
        # 8. Send Result to Frontend/Client
        await websocket.send_json(event)
        logger.info(f"[Stream {session_id}] Event sent: Clone={event['clone_probability']} Transcript='{event['transcript_delta']}'")

    except Exception as e:
        logger.error(f"[Stream {session_id}] Failed to process window {chunk_index}: {e}")
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Could not delete temp file {temp_path}: {e}")
