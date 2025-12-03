# backend/action_engine_plus.py
import random, os

class ActionEnginePlus:
    """Extended action engine that picks visual & audio responses for each emotion."""
    def __init__(self):
        # Map emotion → visual scene & sound file (local or URLs)
        self.scenes = {
            "happy":   {"scene": "sunrise.gif", "sound": "happy.mp3", "message": "Turning on bright ambient lights 🌞"},
            "sad":     {"scene": "rain.gif", "sound": "calm_piano.mp3", "message": "Playing comfort music 🎵"},
            "angry":   {"scene": "fire.gif", "sound": "breathing.mp3", "message": "Dimming lights & suggesting breathing"},
            "fearful": {"scene": "storm.gif", "sound": "relax_waves.mp3", "message": "Locking doors & enabling security 🚨"},
            "calm":    {"scene": "forest.gif", "sound": "birds.mp3", "message": "Maintaining calm environment 🌿"},
            "neutral": {"scene": "space.gif", "sound": "neutral.mp3", "message": "Neutral ambient mode"},
            "disgust": {"scene": "clean.gif", "sound": "fresh_air.mp3", "message": "Activating purifier 🌬️"},
            "surprised": {"scene": "spark.gif", "sound": "surprise.mp3", "message": "Capturing surprise moment ⚡"}
        }

    def get_response(self, emotion: str):
        entry = self.scenes.get(emotion, self.scenes["neutral"])
        # in real IoT: send command to hardware here
        response = {
            "emotion": emotion,
            "message": entry["message"],
            "scene": entry["scene"],
            "sound": entry["sound"]
        }
        print(f"[ActionEngine+] Triggered: {response}")
        return response
