import asyncio
import json
import os
import sys

import nats
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand

from notifications.models import Notification

MAX_DELIVERIES = 5


@sync_to_async
def process_notification(data):
    event_id = data.get("event_id")
    user_id = data.get("user_id")
    email = data.get("email")
    username = data.get("username", "")

    if event_id and Notification.objects.filter(event_id=event_id).exists():
        return False, "duplicate"

    Notification.objects.create(
        event_id=event_id,
        user_id=user_id,
        email=email,
        message=f"Welcome {username}!",
        status="sent",
    )
    return True, "created"


async def consume():
    nats_url = os.getenv("NATS_URL")
    if not nats_url:
        raise RuntimeError("NATS_URL environment variable is required")

    nc = await nats.connect(
        nats_url,
        user=os.getenv("NATS_USER"),
        password=os.getenv("NATS_PASSWORD"),
    )

    js = nc.jetstream()

    try:
        await js.add_stream(
            name="USERS",
            subjects=["users.created", "users.created.dlq"],
        )
        print("Created/verified USERS stream (including DLQ subject)")
    except Exception as e:
        print(f"USERS stream setup notice: {e}")

    try:
        await js.add_consumer(
            stream="USERS",
            durable_name="notification-service",
            filter_subject="users.created",
            ack_policy="explicit",
        )
        print("Created/verified notification consumer")
    except Exception as e:
        print(f"Consumer setup notice: {e}")

    sub = await js.pull_subscribe(
        "users.created",
        durable="notification-service",
    )

    print("Notification Service NATS Consumer is listening...")

    try:
        while True:
            try:
                messages = await sub.fetch(1, timeout=2)

                for msg in messages:
                    try:
                        data = json.loads(msg.data.decode("utf-8"))
                        print("Received event:", data)

                        created, status_type = await process_notification(data)

                        if status_type == "duplicate":
                            print(f"[IDEMPOTENCY] Event {data.get('event_id')} already processed. Skipping DB save and sending ACK.")
                        else:
                            print(f"[SUCCESS] Notification saved successfully for user {data.get('user_id')}")

                        await msg.ack()

                    except Exception as error:
                        num_delivered = msg.metadata.num_delivered if hasattr(msg, "metadata") and msg.metadata else 1
                        print(f"[ERROR] Message processing failed (attempt {num_delivered}): {error}")

                        if num_delivered >= MAX_DELIVERIES:
                            try:
                                await nc.publish("users.created.dlq", msg.data)
                                await nc.flush()
                                print(f"[DLQ] Max delivery attempts ({MAX_DELIVERIES}) reached. Routed to users.created.dlq.")
                                await msg.ack()
                            except Exception as dlq_err:
                                print(f"[DLQ ERROR] Failed to route to DLQ: {dlq_err}")
                        else:
                            print(f"[REDELIVERY] Message will be redelivered by JetStream.")

            except asyncio.TimeoutError:
                pass

    finally:
        await nc.close()


class Command(BaseCommand):
    help = "Run the NATS notification consumer with JetStream, idempotency, and DLQ handling"

    def handle(self, *args, **options):
        try:
            asyncio.run(consume())
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING(
                    "Notification consumer stopped."
                )
            )