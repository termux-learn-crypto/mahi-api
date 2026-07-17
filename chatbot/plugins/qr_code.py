import re
import io
import base64
from datetime import datetime
from pathlib import Path
from . import Plugin


class QRCodePlugin(Plugin):
    def __init__(self):
        super().__init__(
            name="qr_code",
            description="Generate QR codes from text, URLs, or any data - returns base64 or saves to file",
            version="1.0.0",
        )
        self.commands = ["qr", "qrcode", "qr code", "scan"]
        self.keywords = [
            "qr", "qrcode", "qr code", "barcode", "scan", "generate qr",
            "qr banao", "qr code banao",
        ]

    def can_handle(self, intent: str, message: str) -> bool:
        if intent in ("qr_code", "generate_qr"):
            return True
        msg = message.lower()
        return any(kw in msg for kw in self.keywords)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        content = self._extract_content(message)
        if not content:
            return {
                "response": (
                    "📱 QR Code kiske liye banau?\n\n"
                    "Examples:\n"
                    "• 'qr code https://google.com'\n"
                    "• 'qr banao mera naam Rahul'\n"
                    "• 'qr code +919876543210'"
                ),
            }

        try:
            import qrcode
            from qrcode.image.styledpil import StyledPilImage
        except ImportError:
            return {"response": "QR code library install nahi hai! Admin se bolo: `pip install qrcode[pil]`"}

        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(content)
            qr.make(fit=True)

            img = qr.make_image(fill_color="#1a1a2e", back_color="white")
            img = img.convert("RGB")

            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode("utf-8")

            data_dir = Path(__file__).parent.parent.parent / "data" / "qrcodes"
            data_dir.mkdir(parents=True, exist_ok=True)
            filename = f"qr_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = data_dir / filename

            img.save(str(filepath), format="PNG")

            content_preview = content[:60] + "..." if len(content) > 60 else content
            return {
                "response": (
                    f"📱 QR Code ban gaya!\n\n"
                    f"📝 Content: {content_preview}\n"
                    f"💾 Saved: data/qrcodes/{filename}\n"
                    f"🖼 Base64: {img_base64[:50]}... (full data response mein hai)\n\n"
                    f"Scan karne ke liye koi bhi QR scanner use karo!"
                ),
                "data": {
                    "content": content,
                    "filename": filename,
                    "filepath": str(filepath),
                    "base64": img_base64,
                    "size": img.size,
                },
            }

        except Exception as e:
            return {"response": f"QR code banane mein dikkat aa rahi hai! 😔 Error: {str(e)[:100]}"}

    def _extract_content(self, message: str) -> str | None:
        msg = message.strip()
        patterns = [
            r'qr\s*(?:code)?\s+(?:of|for|ka|ko|mein|banao|generate)?\s*(.+)',
            r'(?:banao|generate|create)\s+qr\s*(?:code)?\s*(.+)',
            r'(.+?)\s+ka\s+qr\s*(?:code)?',
        ]
        for pattern in patterns:
            match = re.search(pattern, msg, re.I)
            if match:
                content = match.group(1).strip()
                content = re.sub(
                    r'\b(qr|qrcode|code|banao|generate|create|of|for|ka|ko|mein|scan)\b',
                    '', content, flags=re.I
                ).strip()
                if content:
                    return content
        cleaned = re.sub(
            r'\b(qr|qrcode|qr code|banao|generate|create|scan|ka|ko|mein)\b',
            '', msg, flags=re.I
        ).strip()
        if cleaned and cleaned != msg.strip():
            return cleaned
        return None
