# Mixtape Bug Hunt - Submission

## Git Log

<img width="1087" alt="Git Log" src="https://github.com/user-attachments/assets/581ef9e1-dcad-44ad-b004-6713cb652c1b">

## AI Usage
I was able use the codebase orientation (summarizing files and tracing data flows), understanding complex functions, and reviewing root cause logic. I always reproduced bugs myself before fixing and verified changes with manual testing and edge cases.

## Codebase Map
**Main files and roles:**
- `app.py`: Flask application factory, database initialization, and blueprint registration.
- `models.py`: Defines all SQLAlchemy models (User, Song, Playlist, Rating, ListeningEvent, Notification, Tag) and association tables (`friendships`, `song_tags`, `playlist_entries` with position ordering).
- `routes/`: Thin controllers that handle HTTP requests, call services, and return JSON.
- `services/`: Contains all business logic (where the 5 bugs were located).
- `seed_data.py`: Populates the database with test users, songs, playlists, etc.

**Example Data Flow (Song Rating → Notification):**
POST /songs/<song_id>/rate in routes/songs.py → notification_service.rate_song() → creates Rating record + Notification for the original song sharer.

**Patterns noticed:** All routes immediately delegate to service functions. Business logic is centralized in services/. Many-to-many relationships use association tables with extra columns (e.g., position in playlists).

## Root Cause Analyses

### Issue #1: My listening streak keeps resetting
**How you reproduced it:** Used Flask shell to set a user's `last_listened_at` to a Saturday, then called `record_listening_event` on Sunday. Streak incorrectly reset to 1 instead of increasing.

**How you found the root cause:** Traced from `routes/users.py` → `streak_service.get_streak()` → `update_listening_streak()`. The suspicious weekday condition stood out.

**The root cause:** The line `elif days_since_last == 1 and today.weekday() != 6:` used Python's `weekday()` (where Sunday = 6). This prevented streak continuation when crossing into or on Sundays.

**Your fix and side-effect check:** Removed the `and today.weekday() != 6` condition. Now uses simple `days_since_last == 1`. Verified streak works across all days (including weekends) and correctly resets after gaps. No other streak-related code was changed.

### Issue #3: The same song keeps showing up twice in search
**How you reproduced it:** Searched for a song that has multiple tags → the same song appeared multiple times in results.

**How you found the root cause:** Examined `search_service.search_songs()`. The query joined on `song_tags` without deduplication.

**The root cause:** `.outerjoin(song_tags)` caused duplication for songs with >1 tag. No `distinct()` was used.

**Your fix and side-effect check:** Added `.distinct()` on the Song query and removed the unnecessary join (tags are loaded via relationship in `to_dict()`). Search now returns unique songs. No impact on `get_song()`.

### Issue #4: No notification when friend rates song
**How you reproduced it:** Rated a song shared by another user → no notification appeared for the sharer.

**How you found the root cause:** Compared `add_to_playlist()` (which works) with `rate_song()` in `notification_service.py`.

**The root cause:** `rate_song()` updated/created the Rating but never called `create_notification()`, unlike the playlist function.

**Your fix and side-effect check:** Added notification creation (matching the exact pattern from `add_to_playlist()`) after saving the rating. Verified notifications appear correctly for the song owner. Rating update logic unchanged.

### Issue #5: The last song in a playlist never shows up
**How you reproduced it:** Added multiple songs to a playlist → last song missing from the returned list.

**How you found the root cause:** Examined `get_playlist_songs()` in `playlist_service.py`. The `[:-1]` slice was the clear cause.

**The root cause:** `return [song.to_dict() for song in songs[:-1]]` sliced off the last song in the ordered query results.

**Your fix and side-effect check:** Removed the `[:-1]` slice. Now returns all songs in correct position order. Verified full playlists load completely with no side effects on other playlist functions.
