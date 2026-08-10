import json
import os
import uuid
from datetime import datetime, timezone
import nats


async def publish_user_created(user):
    nats_url = os.getenv("NATS_URL")
    if not nats_url:
        raise RuntimeError("NATS_URL environment variable is not set")

    nc = await nats.connect(
        nats_url,
        user=os.getenv("NATS_USER") or None,
        password=os.getenv("NATS_PASSWORD") or None,
    )

    try:
        event = {
            "event_id": str(uuid.uuid4()),
            "event": "user.created",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await nc.publish(
            "users.created",
            json.dumps(event).encode("utf-8")
        )

        await nc.flush()

    finally:
        await nc.close()