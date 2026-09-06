"""
Spotify metadata extraction module.
Fetches song, album, and playlist metadata without downloading media.
"""

import json
import os
import re
import subprocess
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .paths import get_temp_dir, get_logs_dir
from .env_manager import get_isolated_env


def format_duration(seconds: int) -> str:
    """Format duration in seconds to MM:SS or HH:MM:SS."""
    if not seconds or seconds < 0:
        return "0:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


@dataclass
class TrackInfo:
    track_number: int
    title: str
    artist: str
    album: str
    duration_seconds: int
    duration_str: str
    url: str
    cover_url: Optional[str] = None
    song_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_number": self.track_number,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "duration_seconds": self.duration_seconds,
            "duration_str": self.duration_str,
            "url": self.url,
            "cover_url": self.cover_url,
            "song_id": self.song_id,
        }


@dataclass
class CollectionInfo:
    type: str  # "track", "album", "playlist", "artist"
    title: str
    artist: str
    tracks: List[TrackInfo] = field(default_factory=list)
    cover_url: Optional[str] = None
    total_duration_seconds: int = 0
    total_duration_str: str = "0:00"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "title": self.title,
            "artist": self.artist,
            "cover_url": self.cover_url,
            "total_duration_seconds": self.total_duration_seconds,
            "total_duration_str": self.total_duration_str,
            "track_count": len(self.tracks),
            "tracks": [t.to_dict() for t in self.tracks],
        }


def detect_url_type(url: str) -> str:
    """Determine the type of Spotify URL: 'track', 'album', 'playlist', 'artist', or 'unknown'."""
    url_clean = url.strip().lower()
    if "spotify.com/track/" in url_clean:
        return "track"
    elif "spotify.com/album/" in url_clean:
        return "album"
    elif "spotify.com/playlist/" in url_clean:
        return "playlist"
    elif "spotify.com/artist/" in url_clean:
        return "artist"
    return "unknown"


def fetch_metadata(url: str, timeout: int = 300) -> CollectionInfo:
    """
    Extract metadata for a Spotify URL without downloading media.
    Uses spotdl save command outputting to a temporary JSON file.
    """
    url_type = detect_url_type(url)
    if url_type == "unknown":
        raise ValueError("Invalid URL: Must be a valid Spotify song, album, or playlist URL.")

    temp_id = str(uuid.uuid4())[:8]
    temp_file = get_temp_dir() / f"meta_{temp_id}.spotdl"

    # Run spotdl save to extract metadata into a JSON file
    env = get_isolated_env()
    cmd = [sys.executable, "-m", "spotdl", "save", url, "--save-file", str(temp_file)]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        if proc.returncode != 0 and not temp_file.exists():
            err_msg = proc.stderr.strip() or proc.stdout.strip()
            raise RuntimeError(f"Metadata extraction failed: {err_msg}")

        if not temp_file.exists():
            raise RuntimeError("No metadata could be parsed for this URL.")

        with open(temp_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        if not raw_data:
            raise RuntimeError("Spotify returned an empty song list.")

        # Parse songs into TrackInfo objects
        tracks: List[TrackInfo] = []
        total_duration = 0
        first_item = raw_data[0]
        collection_title = first_item.get("list_name") or first_item.get("album_name") or first_item.get("name") or "Collection"
        collection_artist = first_item.get("album_artist") or first_item.get("artist") or "Various Artists"
        collection_cover = first_item.get("cover_url")

        for idx, item in enumerate(raw_data, start=1):
            dur = int(item.get("duration", 0) or 0)
            total_duration += dur
            artist_str = ", ".join(item.get("artists", [])) if isinstance(item.get("artists"), list) else (item.get("artist") or "Unknown Artist")
            
            t = TrackInfo(
                track_number=item.get("track_number") or idx,
                title=item.get("name") or f"Track {idx}",
                artist=artist_str,
                album=item.get("album_name") or collection_title,
                duration_seconds=dur,
                duration_str=format_duration(dur),
                url=item.get("url") or "",
                cover_url=item.get("cover_url"),
                song_id=item.get("song_id"),
            )
            tracks.append(t)

        return CollectionInfo(
            type=url_type,
            title=collection_title,
            artist=collection_artist,
            tracks=tracks,
            cover_url=collection_cover,
            total_duration_seconds=total_duration,
            total_duration_str=format_duration(total_duration),
        )

    finally:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)
