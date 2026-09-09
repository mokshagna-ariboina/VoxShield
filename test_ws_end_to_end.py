import asyncio
import websockets
import json
import wave
import time
import os

async def simulate_android_stream():
    test_file = r'backend\uploads\0426b1bf-f077-4cb7-9b5e-57c6167eb4b3.wav'
    print(f"Simulating WebRTC using {test_file}")
    
    with wave.open(test_file, 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        audio_data = wf.readframes(n_frames)
        
    print(f"Format: {n_channels} channels, {sampwidth} bytes/sample, {framerate} Hz")
    
    # Send 16000 bytes at a time (500ms at 16kHz)
    chunk_size = 16000  
    
    try:
        async with websockets.connect('ws://127.0.0.1:8000/api/analyze/stream') as ws:
            print("Connected to FastAPI WebSocket.")
            
            async def receive_events():
                try:
                    while True:
                        msg = await ws.recv()
                        event = json.loads(msg)
                        print(f"\n[RECEIVED EVENT]")
                        print(json.dumps(event, indent=2))
                except Exception as e:
                    pass
            
            recv_task = asyncio.create_task(receive_events())
            
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                if len(chunk) < chunk_size:
                    # Pad to chunk size if last chunk is too small
                    chunk += b'\0' * (chunk_size - len(chunk))
                await ws.send(chunk)
                await asyncio.sleep(0.5)
                
            await asyncio.sleep(5) # Wait for final processing
            recv_task.cancel()
            
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(simulate_android_stream())
