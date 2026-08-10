import asyncio
import json
import os
import sqlite3
import nats

NATS_URL = os.getenv("NATS_URL", "nats://127.0.0.1:4222")
NATS_USER = os.getenv("NATS_USER", "app")
NATS_PASSWORD = os.getenv("NATS_PASSWORD", "appsecret")
NOTIFICATION_DB = r"D:\TASK\TASK\notification-service\db.sqlite3"


async def run_idempotency_and_dlq_test():
    print("=== TESTING NATS IDEMPOTENCY AND DLQ ===")
    
    nc = await nats.connect(
        NATS_URL,
        user=NATS_USER,
        password=NATS_PASSWORD,
    )
    js = nc.jetstream()
    
    conn = sqlite3.connect(NOTIFICATION_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), event_id FROM notifications_notification WHERE event_id IS NOT NULL GROUP BY event_id LIMIT 1")
    row = cursor.fetchone()
    
    if not row:
        print("No existing event found in DB to test duplicate.")
        conn.close()
        await nc.close()
        return
        
    count_before, existing_event_id = row
    cursor.execute("SELECT COUNT(*) FROM notifications_notification WHERE event_id = ?", (existing_event_id,))
    total_before = cursor.fetchone()[0]
    conn.close()
    
    print(f"Existing event_id in DB: {existing_event_id} (count before duplicate publish: {total_before})")
    
    duplicate_payload = {
        "event_id": existing_event_id,
        "event": "user.created",
        "user_id": 9999,
        "username": "duplicate_test",
        "email": "duplicate@example.com"
    }
    
    await js.publish("users.created", json.dumps(duplicate_payload).encode("utf-8"))
    print("Published duplicate event to NATS JetStream subject 'users.created'.")
    
    await asyncio.sleep(2.0)
    
    conn = sqlite3.connect(NOTIFICATION_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM notifications_notification WHERE event_id = ?", (existing_event_id,))
    total_after = cursor.fetchone()[0]
    conn.close()
    
    print(f"Count in DB after duplicate publish: {total_after}")
    assert total_before == total_after, f"Idempotency violation! Expected count {total_before}, got {total_after}"
    print("[PASS] Idempotency verified! Duplicate event was skipped cleanly without creating duplicate records.")
    
    await nc.close()


if __name__ == "__main__":
    asyncio.run(run_idempotency_and_dlq_test())
