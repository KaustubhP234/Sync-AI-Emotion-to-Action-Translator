class ActionEngine:
    def trigger_action(self, emotion):
        actions = {
            "happy": "Turning on bright ambient lights 🌞",
            "sad": "Playing your comfort playlist 🎵",
            "angry": "Activating calm mode 🌙",
            "fearful": "Locking doors and enabling security alert 🚨",
            "disgust": "Activating air purifier 🌿",
            "surprised": "Logging surprise event.",
            "calm": "Maintaining calm environment.",
            "neutral": "No action needed."
        }
        return actions.get(emotion, "No defined action.")
