import requests
import json
import base64
import io
import math
from .config import config


class VoiceEngine:
    def __init__(self):
        self.stt_provider = config.STT_PROVIDER
        self.tts_provider = config.TTS_PROVIDER
        self.stt_api_key = config.STT_API_KEY
        self.tts_api_key = config.TTS_API_KEY

        self.voices = {
            "female": {"google": "hi-IN-INR-Temp1-A", "name": "Hindi Female", "emotion": "neutral"},
            "male": {"google": "hi-IN-INR-Temp2-A", "name": "Hindi Male", "emotion": "neutral"},
            "english_female": {"google": "en-US-Wavenet-F", "name": "English Female", "emotion": "neutral"},
            "english_male": {"google": "en-US-Wavenet-D", "name": "English Male", "emotion": "neutral"},
            "child": {"google": "hi-IN-INR-Temp3-A", "name": "Child Voice", "emotion": "happy"},
            "elderly": {"google": "hi-IN-INR-Temp4-A", "name": "Elderly Voice", "emotion": "calm"},
            "energetic": {"google": "en-US-Wavenet-A", "name": "Energetic", "emotion": "excited"},
            "calm": {"google": "en-US-Wavenet-C", "name": "Calm Voice", "emotion": "calm"},
            "whisper": {"google": "en-US-Wavenet-B", "name": "Soft Whisper", "emotion": "sad"},
            "authoritative": {"google": "en-US-Wavenet-E", "name": "Authoritative", "emotion": "neutral"},
        }

        self.emotion_voice_map = {
            "happy": {"pitch": 2.0, "speed": 1.1, "volume_gain": 1.5},
            "sad": {"pitch": -2.0, "speed": 0.9, "volume_gain": 0.8},
            "angry": {"pitch": 3.0, "speed": 1.2, "volume_gain": 2.0},
            "excited": {"pitch": 4.0, "speed": 1.3, "volume_gain": 2.5},
            "calm": {"pitch": 0.0, "speed": 0.95, "volume_gain": 1.0},
            "neutral": {"pitch": 0.0, "speed": 1.0, "volume_gain": 1.0},
            "fearful": {"pitch": 1.0, "speed": 1.15, "volume_gain": 0.7},
            "confused": {"pitch": 0.5, "speed": 0.95, "volume_gain": 1.0},
        }

        self.supported_languages = {
            "hi": "hi-IN",
            "en": "en-US",
            "hinglish": "hi-IN",
            "ta": "ta-IN",
            "te": "te-IN",
            "bn": "bn-IN",
            "mr": "mr-IN",
        }

    def transcribe(self, audio_data: bytes, language: str = "hi-IN") -> dict:
        try:
            if self.stt_provider == "google":
                return self._google_stt(audio_data, language)
            elif self.stt_provider == "whisper":
                return self._whisper_stt(audio_data, language)
        except Exception as e:
            return {"error": f"STT failed: {str(e)}", "text": ""}
        return {"error": "No STT provider configured", "text": ""}

    def _google_stt(self, audio_data: bytes, language: str) -> dict:
        if not self.stt_api_key:
            return self._fallback_stt(audio_data)

        url = f"https://speech.googleapis.com/v1/speech:recognize?key={self.stt_api_key}"
        audio_b64 = base64.b64encode(audio_data).decode()
        payload = {
            "config": {
                "encoding": "LINEAR16",
                "sampleRateHertz": 16000,
                "languageCode": language,
                "alternativeLanguageCodes": ["hi-IN", "en-US"],
                "enableAutomaticPunctuation": True,
                "model": "latest_short",
                "enableWordTimeOffsets": True,
            },
            "audio": {"content": audio_b64},
        }
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                transcript = results[0]["alternatives"][0]["transcript"]
                confidence = results[0]["alternatives"][0].get("confidence", 0.8)
                return {"text": transcript, "confidence": confidence, "provider": "google"}
        return {"error": "Google STT failed", "text": ""}

    def _whisper_stt(self, audio_data: bytes, language: str) -> dict:
        if not self.stt_api_key:
            return self._fallback_stt(audio_data)

        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.stt_api_key}"}
        files = {"file": ("audio.wav", audio_data, "audio/wav")}
        data = {"model": "whisper-1", "language": language[:2]}
        resp = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        if resp.status_code == 200:
            transcript = resp.json().get("text", "")
            return {"text": transcript, "confidence": 0.9, "provider": "whisper"}
        return {"error": "Whisper STT failed", "text": ""}

    def _fallback_stt(self, audio_data: bytes) -> dict:
        return {
            "text": "",
            "confidence": 0,
            "provider": "none",
            "message": "STT API key not configured. Audio received but cannot transcribe.",
        }

    def synthesize(self, text: str, voice: str = "female",
                   language: str = "hi-IN", speed: float = 1.0,
                   emotion: str = None) -> dict:
        try:
            if emotion and emotion in self.emotion_voice_map:
                emotion_settings = self.emotion_voice_map[emotion]
                speed *= emotion_settings["speed"]

            if self.tts_provider == "google":
                return self._google_tts(text, voice, language, speed, emotion)
            elif self.tts_provider == "elevenlabs":
                return self._elevenlabs_tts(text, voice, emotion)
        except Exception as e:
            return {"error": f"TTS failed: {str(e)}", "audio": None}
        return {"error": "No TTS provider configured", "audio": None}

    def _google_tts(self, text: str, voice: str, language: str, speed: float, emotion: str = None) -> dict:
        if not self.tts_api_key:
            return self._fallback_tts(text)

        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.tts_api_key}"
        voice_config = self.voices.get(voice, self.voices["female"])
        voice_name = voice_config.get("google", "hi-IN-INR-Temp1-A")

        pitch = 0.0
        if emotion and emotion in self.emotion_voice_map:
            pitch = self.emotion_voice_map[emotion]["pitch"]

        payload = {
            "input": {"text": text},
            "voice": {
                "languageCode": language,
                "name": voice_name,
                "ssmlGender": "FEMALE" if "female" in voice else "MALE",
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": speed,
                "pitch": pitch,
            },
        }
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            audio_b64 = resp.json().get("audioContent", "")
            return {
                "audio": audio_b64,
                "format": "mp3",
                "provider": "google",
                "voice": voice,
                "emotion": emotion,
                "speed": speed,
            }
        return {"error": "Google TTS failed", "audio": None}

    def _elevenlabs_tts(self, text: str, voice: str, emotion: str = None) -> dict:
        if not self.tts_api_key:
            return self._fallback_tts(text)

        voice_ids = {
            "female": "21m00Tcm4TlvDq8ikWAM",
            "male": "pNInz6obpgDQGcFmaJgB",
            "child": "EXAVITQu4vr4xnSDxMaL",
            "energetic": "MF3mGyEYCl7XYWbV9V6O",
            "calm": "AZnzlk1XvdvUeBnXmlld",
        }
        voice_id = voice_ids.get(voice, voice_ids["female"])
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {"xi-api-key": self.tts_api_key, "Content-Type": "application/json"}
        payload = {"text": text, "model_id": "eleven_multilingual_v2"}
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            audio_b64 = base64.b64encode(resp.content).decode()
            return {
                "audio": audio_b64,
                "format": "mp3",
                "provider": "elevenlabs",
                "voice": voice,
                "emotion": emotion,
            }
        return {"error": "ElevenLabs TTS failed", "audio": None}

    def _fallback_tts(self, text: str) -> dict:
        return {
            "audio": None,
            "format": "mp3",
            "provider": "none",
            "message": "TTS API key not configured.",
            "text": text,
        }

    def synthesize_with_emotion(self, text: str, emotion: str, voice: str = "female",
                                 language: str = "hi-IN") -> dict:
        return self.synthesize(text, voice=voice, language=language, emotion=emotion)

    def get_voices(self) -> dict:
        return {
            "available": list(self.voices.keys()),
            "details": self.voices,
            "emotions": list(self.emotion_voice_map.keys()),
        }

    def set_voice(self, voice: str) -> bool:
        if voice in self.voices:
            return True
        return False

    def get_supported_languages(self) -> dict:
        return self.supported_languages

    def filter_noise(self, audio_data: bytes) -> bytes:
        return audio_data

    def clone_voice(self, user_id: str, audio_samples: list[bytes]) -> dict:
        return {
            "status": "not_configured",
            "message": "Voice cloning requires ElevenLabs API key",
            "user_id": user_id,
        }

    def get_emotion_for_text(self, text: str) -> str:
        text_lower = text.lower()

        happy_words = ["happy", "khush", "achha", "great", "awesome", "love"]
        sad_words = ["sad", "dukh", "sorry", "miss", "heartbreak"]
        angry_words = ["angry", "gussa", "frustrated", "stupid", "hate"]
        excited_words = ["excited", "wow", "amazing", "fantastic", "celebrate"]

        if any(w in text_lower for w in happy_words):
            return "happy"
        elif any(w in text_lower for w in sad_words):
            return "sad"
        elif any(w in text_lower for w in angry_words):
            return "angry"
        elif any(w in text_lower for w in excited_words):
            return "excited"
        return "neutral"
