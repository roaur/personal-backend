from datetime import datetime

def json_serializer(json_to_post: dict) -> dict:
    if isinstance(json_to_post, datetime):
        return json_to_post.isoformat()
