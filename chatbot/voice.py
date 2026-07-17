import requests
import json
import base64
import io
from .config import config


class VoiceEngine:
    def __init__(self):
        self.stt_provider = config.STT_PROVIDER
        self.tts_provider = config.TTS_PROVIDER
        self.stt_api_key = config.STT_API_KEY
        self.tts_api_key = config.TTS_API_KEY

        self.voices = {
            "female": {"google": "hi-IN-INR-Temp1-A", "name": "Hindi Female"},
            "male": {"google": "hi-IN-INR-Temp2-A", "name": "Hindi Male"},
            "english_female": {"google": "en-US-Wavenet-F", "name": "English Female"},
            "english_male": {"google": "en-US-Wavenet-D", "name": "English Male"},
        }

        self.supported_languages = {
            "hi": "hi-IN",
            "en": "en-US",
            "hinglish": "hi-IN",
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
                   language: str = "hi-IN", speed: float = 1.0) -> dict:
        try:
            if self.tts_provider == "google":
                return self._google_tts(text, voice, language, speed)
            elif self.tts_provider == "elevenlabs":
                return self._elevenlabs_tts(text, voice)
        except Exception as e:
            return {"error": f"TTS failed: {str(e)}", "audio": None}
        return {"error": "No TTS provider configured", "audio": None}

    def _google_tts(self, text: str, voice: str, language: str, speed: float) -> dict:
        if not self.tts_api_key:
            return self._fallback_tts(text)

        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.tts_api_key}"
        voice_config = self.voices.get(voice, self.voices["female"])
        voice_name = voice_config.get("google", "hi-IN-INR-Temp1-A")

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
                "pitch": 0.0,
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
            }
        return {"error": "Google TTS failed", "audio": None}

    def _elevenlabs_tts(self, text: str, voice: str) -> dict:
        if not self.tts_api_key:
            return self._fallback_tts(text)

        voice_ids = {
            "female": "21m00Tcm4TlvDq8ikWAM",
            "male": "pNInz6obpgDQGcFmaJgB",
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

    def get_voices(self) -> dict:
        return {
            "available": list(self.voices.keys()),
            "details": self.voices,
        }

    def set_voice(self, voice: str) -> bool:
        if voice in self.voices:
            return True
        return False

    def get_supported_languages(self) -> dict:
        return self.supported_languages
