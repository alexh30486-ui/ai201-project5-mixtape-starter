from app import db
from models import Notification, Rating, Song, User


def create_notification(user_id: str, notification_type: str, body: str) -> Notification:
    """Create a notification row for a user."""
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        body=body,
    )
    db.session.add(notification)
    db.session.commit()
    return notification


def rate_song(user_id: str, song_id: str, score: int) -> Rating:
    """
    Save a user's rating for a song and notify the original sharer.
    """
    if score < 1 or score > 5:
        raise ValueError("Score must be between 1 and 5")

    song = db.session.get(Song, song_id)
    if not song:
        raise ValueError(f"Song {song_id} not found")

    rater = db.session.get(User, user_id)
    if not rater:
        raise ValueError(f"User {user_id} not found")

    existing = db.session.query(Rating).filter_by(
        user_id=user_id,
        song_id=song_id,
    ).first()

    if existing:
        existing.score = score
        rating = existing
    else:
        rating = Rating(user_id=user_id, song_id=song_id, score=score)
        db.session.add(rating)

    db.session.commit()

    if song.shared_by != user_id:
        create_notification(
            user_id=song.shared_by,
            notification_type="song_rated",
            body=f"{rater.username} rated your song '{song.title}' {score}/5.",
        )

    return rating


def get_notifications(user_id: str, unread_only: bool = False) -> list[dict]:
    """Return notifications for a user, optionally limited to unread ones."""
    user = db.session.get(User, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    query = db.session.query(Notification).filter_by(user_id=user_id)
    if unread_only:
        query = query.filter_by(read=False)

    notifications = query.order_by(Notification.created_at.desc()).all()
    return [notification.to_dict() for notification in notifications]


def mark_as_read(notification_id: str) -> Notification:
    """Mark a notification as read."""
    notification = db.session.get(Notification, notification_id)
    if not notification:
        raise ValueError(f"Notification {notification_id} not found")

    notification.read = True
    db.session.commit()
    return notification