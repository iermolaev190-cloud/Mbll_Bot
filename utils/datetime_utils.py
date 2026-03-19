from datetime import datetime, timezone

def utcnow():
    """Асинхронно-безопасная замена datetime.utcnow()"""
    return datetime.now(timezone.utc).replace(tzinfo=None)