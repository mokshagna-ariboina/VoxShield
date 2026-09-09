package com.example.voxshield

object Config {
    // CHANGE THIS TO YOUR LOCAL LAPTOP IP ADDRESS
const val SIGNALING_SERVER_IP = "192.168.29.34"    
    // Signaling for WebRTC
    const val SIGNALING_SERVER_URL = "ws://${SIGNALING_SERVER_IP}:8765"
    
    // VoxShield Analysis Backend WebSocket (FastAPI)
    const val ANALYSIS_SERVER_URL = "ws://${SIGNALING_SERVER_IP}:8000/api/analyze/stream"
}
