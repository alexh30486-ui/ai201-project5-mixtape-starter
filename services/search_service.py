"""
services/search_service.py
Song search logic.
"""

from app import db
from models import Song, song_tags


def search_songs(query: str) -> list[dict]:
    """
    Search for songs by title or artist (case-insensitive).
    Returns each matching song once, with its tags.
    """
    results = (
        db.session.query(Song)
        .filter(
            db.or_(
                Song.title.ilike(f"%{query}%"),
                Song.artist.ilike(f"%{query}%"),
            )
        )
        .distinct()          # Prevents duplicates from tags join
        .all()
    )
    return [song.to_dict() for song in results]


def get_song(song_id: str) -> dict:
    """Get a single song by ID."""
    song = db.session.get(Song, song_id)
    if not song:
        raise ValueError(f"Song {song_id} not found")
    return song.to_dict()