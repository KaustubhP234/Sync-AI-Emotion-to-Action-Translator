# backend/drift_detector.py
from typing import List, Dict, Any
import math

# A canonical ordering of emotions — used only to compute a simple numeric "distance".
# You can reorder to better reflect semantic similarity if you prefer.
EMOTION_ORDER = [
    "neutral", "calm", "happy", "surprised",   # positive/neutral cluster
    "sad", "fearful", "angry", "disgust"       # negative cluster
]

_emotion_to_idx = {e: i for i, e in enumerate(EMOTION_ORDER)}

class EmotionDriftDetector:
    """
    Simple drift detector that:
     - converts emotion labels to indices
     - computes absolute differences between consecutive indices as 'drift magnitude'
     - flags a drift event when magnitude >= drift_threshold
    """

    def __init__(self, drift_threshold: int = 2):
        """
        drift_threshold: integer difference in emotion index to consider a 'drift event'.
                         (2 is moderate: e.g. calm->sad, happy->angry)
        """
        self.drift_threshold = drift_threshold

    def _to_idx(self, emotion: str) -> int:
        return _emotion_to_idx.get(emotion, 0)

    def analyze_sequence(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        history: list of rows ordered newest-first or oldest-first. We'll use oldest-first.
        Each row is expected to contain keys: 'timestamp', 'emotion', 'confidence', 'action', ...
        Returns:
            {
              "avg_drift": float,
              "stability": float,   # 0-100, higher = more stable
              "drift_events": [ {from,to,ts_from,ts_to,magnitude}, ... ],
              "avg_confidence": float,
              "entries": int
            }
        """
        if not history:
            return {
                "avg_drift": 0.0,
                "stability": 100.0,
                "drift_events": [],
                "avg_confidence": 0.0,
                "entries": 0
            }

        # Ensure oldest-first
        rows = list(reversed(history))

        indices = [self._to_idx(r.get("emotion", "neutral")) for r in rows]
        confidences = [float(r.get("confidence") or 0) for r in rows]

        drifts = []
        drift_events = []
        for i in range(1, len(indices)):
            mag = abs(indices[i] - indices[i - 1])
            drifts.append(mag)
            # if magnitude exceeds threshold, log an event
            if mag >= self.drift_threshold:
                drift_events.append({
                    "from": rows[i - 1].get("emotion"),
                    "to": rows[i].get("emotion"),
                    "ts_from": rows[i - 1].get("timestamp"),
                    "ts_to": rows[i].get("timestamp"),
                    "magnitude": mag
                })

        avg_drift = float(sum(drifts) / len(drifts)) if drifts else 0.0
        # Convert avg_drift into a 0-100 stability score: smaller avg_drift => higher stability.
        # We choose a scaling such that avg_drift == 0 -> 100, avg_drift >= max_possible (len(EMOTION_ORDER)-1) -> 0
        max_possible = max(1, len(EMOTION_ORDER) - 1)
        stability = max(0.0, 100.0 * (1.0 - (avg_drift / max_possible)))
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "avg_drift": round(avg_drift, 3),
            "stability": round(stability, 2),
            "drift_events": drift_events,
            "avg_confidence": round(avg_confidence, 2),
            "entries": len(rows)
        }
