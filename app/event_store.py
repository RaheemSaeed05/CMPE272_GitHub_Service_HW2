#Raheem, webhook

from datetime import datetime, timezone

events = []
processed_deliveries = set()


def save_event(delivery_id, event, action, issue_number):
    key = (delivery_id, action)

    # Ignore the same webhook delivery if GitHub sends it again.
    if key in processed_deliveries:
        return False

    processed_deliveries.add(key)

    events.append({
        "id": delivery_id,
        "event": event,
        "action": action,
        "issue_number": issue_number,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    return True


# Liuyiyi Jin — return only the most recent webhook deliveries for debugging.
def get_events(limit: int = 20):
    return list(reversed(events[-limit:]))
