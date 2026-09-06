"""VoxShield FastAPI application factory."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analyze, liveness, calls, speakers, trust, transactions

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML models on startup, clean up on shutdown."""
    logger.info("Starting VoxShield — loading ML models...")

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # --- AASIST deepfake detector ---
    from app.services.aasist_detector import AASISTDetector
    app.state.aasist_detector = AASISTDetector(
        config_path=settings.AASIST_CONFIG_PATH,
        checkpoint_path=settings.AASIST_CHECKPOINT_PATH,
    )

    # --- Whisper speech-to-text ---
    from app.services.whisper_transcriber import WhisperTranscriber
    app.state.whisper_transcriber = WhisperTranscriber(
        model_size=settings.WHISPER_MODEL_SIZE,
    )

    # --- Social-engineering language analyzer ---
    from app.services.language_analyzer import LanguageAnalyzer
    app.state.language_analyzer = LanguageAnalyzer()

    # --- Risk engine (signal fusion) ---
    from app.services.risk_engine import RiskEngine
    app.state.risk_engine = RiskEngine(
        weights={
            "clone_probability": settings.WEIGHT_CLONE,
            "social_engineering_score": settings.WEIGHT_SOCIAL_ENG,
            "speaker_mismatch_score": settings.WEIGHT_SPEAKER,
            "trust_novelty_score": settings.WEIGHT_TRUST,
            "transaction_risk_score": settings.WEIGHT_TRANSACTION,
        },
        pass_threshold=settings.RISK_THRESHOLD_PASS,
        challenge_threshold=settings.RISK_THRESHOLD_CHALLENGE,
    )

    # --- Liveness challenge service ---
    from app.services.liveness_service import LivenessService
    app.state.liveness_service = LivenessService()

    # --- Speaker verifier (Tier 2 — may not be available) ---
    from app.services.speaker_verifier import SpeakerVerifier
    app.state.speaker_verifier = SpeakerVerifier()

    # --- Transaction guard (Tier 2) ---
    from app.services.transaction_guard import TransactionGuard
    app.state.transaction_guard = TransactionGuard()

    logger.info("All services loaded. VoxShield is ready.")
    yield

    # Cleanup
    logger.info("Shutting down VoxShield...")
    app.state.aasist_detector = None
    app.state.whisper_transcriber = None
    app.state.language_analyzer = None
    app.state.risk_engine = None
    app.state.liveness_service = None
    app.state.speaker_verifier = None
    app.state.transaction_guard = None


app = FastAPI(
    title="VoxShield API",
    description="AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — permissive for demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(analyze.router, prefix="/api")
app.include_router(liveness.router, prefix="/api")
app.include_router(calls.router, prefix="/api")
app.include_router(speakers.router, prefix="/api")
app.include_router(trust.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint returning project info."""
    return {
        "name": "VoxShield API",
        "version": "1.0.0",
        "description": "AI-Powered Voice Cloning Fraud Detection",
        "docs": "/docs",
    }
