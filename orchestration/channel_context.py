"""Channel Context Manager — loads and manages per-channel configuration."""

import json
import os
from typing import Any, Dict, List, Optional

DEFAULT_CHANNELS = {
    "geo-daily-ur": {
        "channel_id": "geo-daily-ur",
        "channel_name": "Geo Daily Urdu",
        "purpose": "Daily geopolitical analysis with maps, Urdu narration, source-backed claims",
        "target_country": "Pakistan",
        "target_audience": "Urdu speakers interested in defense, borders, international relations",
        "topic_focus": "Indo-Pak border, Kashmir, UN statements, satellite imagery",
        "language": "ur",
        "secondary_language": "en",
        "upload_day": "Monday",
        "upload_time": "18:00",
        "timezone": "Asia/Karachi",
        "review_required": True,
        "policy_version": "2026-11-24",
        "is_monetized": True,
        "search_context": {
            "last_search_date": "",
            "last_search_query": "",
            "feeds_configured": ["ISPR", "PIB", "MEA", "UNMOGIP", "GDELT", "NASA FIRMS"],
            "keywords": ["LoC", "ceasefire", "Kashmir", "satellite", "artillery", "troop movement"],
        },
        "render_template": "map_heavy",
        "tags": ["render_heavy"],
    },
    "tech-tutorials-hi": {
        "channel_id": "tech-tutorials-hi",
        "channel_name": "Tech Tutorials Hindi",
        "purpose": "Step-by-step tech tutorials in Hindi/Hinglish",
        "target_country": "India",
        "target_audience": "Hindi speakers interested in mobile tricks, laptop fixes, app tutorials",
        "topic_focus": "Mobile tricks, laptop repair, app tutorials, software tips",
        "language": "hi",
        "secondary_language": "en",
        "upload_day": "Wednesday",
        "upload_time": "18:00",
        "timezone": "Asia/Kolkata",
        "review_required": True,
        "policy_version": "2026-11-24",
        "is_monetized": False,
        "search_context": {
            "last_search_date": "",
            "last_search_query": "",
            "feeds_configured": ["TechCrunch", "The Verge", "GitHub Trending", "Product Hunt"],
            "keywords": ["mobile trick", "laptop fix", "app tutorial", "software tip"],
        },
        "render_template": "screen_capture",
        "tags": [],
    },
    "islamic-history-ur": {
        "channel_id": "islamic-history-ur",
        "channel_name": "Islamic History Urdu",
        "purpose": "Narrative documentaries on Islamic history in Urdu",
        "target_country": "Pakistan",
        "target_audience": "Urdu speakers interested in Islamic history, Urdu literature",
        "topic_focus": "Islamic history, Urdu adab, ghazal, historical figures",
        "language": "ur",
        "secondary_language": "en",
        "upload_day": "Friday",
        "upload_time": "15:00",
        "timezone": "Asia/Dubai",
        "review_required": True,
        "policy_version": "2026-11-24",
        "is_monetized": False,
        "search_context": {
            "last_search_date": "",
            "last_search_query": "",
            "feeds_configured": ["History books", "Urdu poetry archives", "Islamic history sources"],
            "keywords": ["Islamic history", "Urdu adab", "ghazal", "historical figure"],
        },
        "render_template": "calligraphy",
        "tags": ["render_heavy"],
    },
}


class ChannelContextManager:
    """Manages per-channel configuration and context."""

    def __init__(self, data_dir: str = "data/channels"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._ensure_defaults()

    def _ensure_defaults(self):
        for ch_id, ctx in DEFAULT_CHANNELS.items():
            path = os.path.join(self.data_dir, ch_id, "context.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if not os.path.exists(path):
                with open(path, "w") as f:
                    json.dump(ctx, f, indent=2, ensure_ascii=False)

    def get_context(self, channel_id: str) -> Optional[Dict[str, Any]]:
        path = os.path.join(self.data_dir, channel_id, "context.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return DEFAULT_CHANNELS.get(channel_id)

    def list_channels(self) -> List[Dict[str, Any]]:
        channels = []
        for ch_id in DEFAULT_CHANNELS:
            ctx = self.get_context(ch_id)
            if ctx:
                channels.append({
                    "channel_id": ctx["channel_id"],
                    "channel_name": ctx["channel_name"],
                    "language": ctx["language"],
                    "purpose": ctx["purpose"],
                })
        return channels

    def update_context(self, channel_id: str, updates: Dict[str, Any]):
        ctx = self.get_context(channel_id)
        if ctx:
            ctx.update(updates)
            path = os.path.join(self.data_dir, channel_id, "context.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump(ctx, f, indent=2, ensure_ascii=False)
