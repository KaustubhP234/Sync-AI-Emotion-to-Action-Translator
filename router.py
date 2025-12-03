# backend/router.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.emotion_model import EmotionModel
from backend.action_engine import ActionEngine
from backend import history_db
from backend.drift_detector import EmotionDriftDetector
from transformers import pipeline
from pydantic import BaseModel
from typing import Optional

emotion_router = APIRouter()
model = EmotionModel()
engine = ActionEngine()
classifier = pipeline("sentiment-analysis")
drift_detector = EmotionDriftDetector()
history_db.init_db()

class AlertPayload(BaseModel):
    from_emotion: str
    to_emotion: str
    magnitude: int
    confidence_from: Optional[float] = None
    confidence_to: Optional[float] = None
    metadata: Optional[str] = ""

@emotion_router.post("/analyze_audio")
async def analyze_audio(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        emotion, confidence = model.predict_audio(audio_bytes)
        action = engine.trigger_action(emotion)
        history_db.log_prediction("audio", file.filename, emotion, confidence, action)
        return {
            "emotion": emotion,
            "confidence": f"{confidence}%",
            "action": action,
            "drift_alert": {"alert": False, "message": "Minor or no emotional change detected."}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@emotion_router.post("/analyze_text")
async def analyze_text(text: str = Form(...)):
    try:
        result = classifier(text)[0]
        emotion = result["label"].lower()
        confidence = round(float(result["score"]) * 100, 2)
        action = engine.trigger_action(emotion)
        history_db.log_prediction("text", "", emotion, confidence, action)
        return {"emotion": emotion, "confidence": f"{confidence}%", "action": action, "drift_alert": {"alert": False, "message": ""}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@emotion_router.get("/history")
def get_history(limit: int = 50):
    rows = history_db.get_history(limit=limit)
    return {"history": rows}

@emotion_router.get("/stability")
def get_stability(limit: int = 50):
    rows = history_db.get_history(limit=limit)
    metrics = drift_detector.analyze_sequence(rows)
    return {"stability": metrics}

# NEW: receive client-side alerts and store
@emotion_router.post("/log_alert")
def log_alert(payload: AlertPayload):
    history_db.log_alert(
        payload.from_emotion,
        payload.to_emotion,
        payload.magnitude,
        payload.confidence_from,
        payload.confidence_to,
        payload.metadata or ""
    )
    return {"status": "ok"}

@emotion_router.get("/alerts")
def get_alerts(limit: int = 50):
    rows = history_db.get_alerts(limit=limit)
    return {"alerts": rows}
