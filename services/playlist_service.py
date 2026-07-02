"""
services/playlist_service.py — Mixtape
Handles playlist creation and retrieval logic.
"""

from app import db
from models import Playlist, Song, User, playlist_entries
from sqlalchemy import asc


def create_playlist(name: str, created_by_user_id: str, is_collaborative: bool = True) -> Playlist:
    """Create a new playlist."""
    user = db.session.get(User, created_by_user_id)
    if not user:
        raise ValueError(f"User {created_by_user_id} not found")

    playlist = Playlist(
        name=name,
        created_by=created_by_user_id,
        is_collaborative=is_collaborative,
    )
    db.session.add(playlist)
    db.session.commit()
    return playlist


def get_playlist_songs(playlist_id: str) -> list[dict]:
    """Get the ordered list of songs in a playlist."""
    playlist = db.session.get(Playlist, playlist_id)
    if not playlist:
        raise ValueError(f"Playlist {playlist_id} not found")

    songs = (
        db.session.query(Song)
        .join(playlist_entries, Song.id == playlist_entries.c.song_id)
        .filter(playlist_entries.c.playlist_id == playlist_id)
        .order_by(asc(playlist_entries.c.position))
        .all()
    )

    return [song.to_dict() for song in songs]  # Fixed: no more [:-1]


def get_playlist(playlist_id: str) -> dict:
    """Get a playlist's metadata."""
    playlist = db.session.get(Playlist, playlist_id)
    if not playlist:
        raise ValueError(f"Playlist {playlist_id} not found")

    return playlist.to_dict()


def get_user_playlists(user_id: str) -> list[dict]:
    """Return all playlists created by a user."""
    user = db.session.get(User, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    playlists = db.session.query(Playlist).filter_by(created_by=user_id).all()
    return [playlist.to_dict() for playlist in playlists]


def add_to_playlist(playlist_id: str, song_id: str, added_by: str) -> None:
    """Add a song to a playlist at the end of the ordering."""
    playlist = db.session.get(Playlist, playlist_id)
    if not playlist:
        raise ValueError(f"Playlist {playlist_id} not found")

    song = db.session.get(Song, song_id)
    if not song:
        raise ValueError(f"Song {song_id} not found")

    user = db.session.get(User, added_by)
    if not user:
        raise ValueError(f"User {added_by} not found")

    position = (
        db.session.query(playlist_entries.c.position)
        .filter(playlist_entries.c.playlist_id == playlist_id)
        .count()
        + 1
    )

    db.session.execute(
        playlist_entries.insert().values(
            playlist_id=playlist_id,
            song_id=song_id,
            position=position,
            added_by=added_by,
        )
    )
    db.session.commit()
