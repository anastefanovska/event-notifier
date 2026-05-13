import requests
import json
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = "https://avalonbooking.mk/services/exportdata.asmx/GetGroupedEvents"

STATE_FILE = "seen.txt"

headers = {
    "Content-Type": "application/json; charset=UTF-8"
}

response = requests.post(API_URL, headers=headers, json={})
print("Status:", response.status_code)
print("Response:", response.text[:500])
data = response.json()

groups = data.get("d", [])
print("Groups found:", len(groups))

current_ids = []

for group in groups:
    events = group.get("Events", [])

    for event in events:
        event_id = str(event.get("Id"))
        name = event.get("NameFirst")

        current_ids.append(event_id)

# Load seen IDs
try:
    with open(STATE_FILE, "r") as f:
        seen_ids = set(f.read().splitlines())
except:
    seen_ids = set()

new_ids = [x for x in current_ids if x not in seen_ids]

# Send notification only for new events
if new_ids:
    for group in groups:
        for event in group.get("Events", []):
            event_id = str(event.get("Id"))

            if event_id in new_ids:
                message = (
                    f"🎟️ NEW EVENT!\n\n"
                    f"{event.get('NameFirst')}\n"
                    f"{event.get('Date')}"
                )

                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    data={
                        "chat_id": CHAT_ID,
                        "text": message
                    }
                )

# Save current IDs
with open(STATE_FILE, "w") as f:
    f.write("\n".join(current_ids))