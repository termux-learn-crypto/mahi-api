from .telegram import TelegramIntegration
from .whatsapp import WhatsAppIntegration
from .slack import SlackIntegration
from .discord import DiscordIntegration

__all__ = [
    "TelegramIntegration",
    "WhatsAppIntegration",
    "SlackIntegration",
    "DiscordIntegration",
]
