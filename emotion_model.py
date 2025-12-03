import os, io
import torch
import torch.nn as nn
import numpy as np
import librosa, joblib

MODEL_PATH = "models/emotion_model.pth"
LABEL_ENCODER_PATH = "models/label_encoder.pkl"
SCALER_PATH = "models/feature_scaler.pkl"

class EmotionCNN(nn.Module):
    def __init__(self, num_classes=8):
        super().__init__()
        self.conv1 = nn.Conv1d(1, 16, 3, padding=1)
        self.bn1 = nn.BatchNorm1d(16)
        self.conv2 = nn.Conv1d(16, 32, 3, padding=1)
        self.bn2 = nn.BatchNorm1d(32)
        self.pool = nn.MaxPool1d(2)
        self.dropout = nn.Dropout(0.3)
        self.relu = nn.ReLU()
        self.fc1 = nn.Linear(32 * 10, 128)
        self.fc2 = nn.Linear(128, num_classes)
    def forward(self, x):
        if len(x.shape) == 2: x = x.unsqueeze(1)
        x = self.pool(self.relu(self.bn1(self.conv1(x))))
        x = self.pool(self.relu(self.bn2(self.conv2(x))))
        x = x.view(x.size(0), -1)
        x = self.dropout(self.relu(self.fc1(x)))
        return self.fc2(x)

class EmotionModel:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = EmotionCNN(num_classes=8).to(self.device)
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError("Model file missing. Run train_emotion_model.py first.")
        self.model.load_state_dict(torch.load(MODEL_PATH, map_location=self.device))
        self.model.eval()
        self.label_encoder = joblib.load(LABEL_ENCODER_PATH)
        self.scaler = joblib.load(SCALER_PATH)
        print("✅ Emotion model loaded successfully")

    def extract_features(self, audio_bytes):
        try:
            stream = io.BytesIO(audio_bytes)
            y, sr = librosa.load(stream, sr=None)
            if len(y) == 0:
                raise ValueError("Empty audio.")
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
            return np.mean(mfcc.T, axis=0)
        except Exception as e:
            print(f"❌ Feature extraction error: {e}")
            return np.zeros(40)

    def predict_audio(self, audio_bytes):
        features = self.extract_features(audio_bytes)
        X_scaled = self.scaler.transform([features])
        X_tensor = torch.tensor(X_scaled, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            out = self.model(X_tensor)
            probs = torch.softmax(out, dim=1)
            conf, pred = torch.max(probs, dim=1)
        emotion = self.label_encoder.inverse_transform(pred.cpu().numpy())[0]
        confidence = round(float(conf.cpu().numpy()) * 100, 2)
        print(f"🎯 Predicted: {emotion} ({confidence}%)")
        return emotion, confidence
