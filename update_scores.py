import os
import json
import requests
from datetime import datetime, timezone

JSONBIN_BIN_ID = os.environ["JSONBIN_BIN_ID"]
JSONBIN_MASTER_KEY = os.environ["JSONBIN_MASTER_KEY"]

# Masters 2026 tournament ID confirmed from ESPN API
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/golf/pga/scoreboard?dates=20260413"

PARTICIPANTS = [
    {"name":"Adrian","picks":["Patrick Reed","Jake Knapp","Harris English","Jason Day","Max Homa"]},
    {"name":"Alex Byrne","picks":["Scottie Scheffler","Jon Rahm","Ludvig Åberg","Hideki Matsuyama","Corey Conners"]},
    {"name":"Conor Cassidy","picks":["Scottie Scheffler","Collin Morikawa","Hideki Matsuyama","Corey Conners","Sungjae Im"]},
    {"name":"Conor Treacy","picks":["Ludvig Åberg","Matt Fitzpatrick","Tommy Fleetwood","Patrick Reed","Nicolai Højgaard"]},
    {"name":"Cormac","picks":["Matt Fitzpatrick","Cameron Young","Si Woo Kim","Jacob Bridgeman","Corey Conners"]},
    {"name":"Daniel Woods","picks":["Jon Rahm","Xander Schauffele","Matt Fitzpatrick","Tommy Fleetwood","Cameron Smith"]},
    {"name":"Donal McMahon","picks":["Jon Rahm","Ludvig Åberg","Xander Schauffele","Patrick Reed","Jordan Spieth"]},
    {"name":"Eanna","picks":["Bryson DeChambeau","Xander Schauffele","Matt Fitzpatrick","Akshay Bhatia","Gary Woodland"]},
    {"name":"Harry","picks":["Xander Schauffele","Jacob Bridgeman","Nicolai Højgaard","Sungjae Im","Ryan Fox"]},
    {"name":"JJ Walshe","picks":["Scottie Scheffler","Jon Rahm","Ludvig Åberg","Si Woo Kim","Russell Henley"]},
    {"name":"Jody","picks":["Ludvig Åberg","Cameron Young","Justin Rose","Nicolai Højgaard","Corey Conners"]},
    {"name":"Macey","picks":["Ludvig Åberg","Cameron Young","Justin Rose","Akshay Bhatia","J.J. Spaun"]},
    {"name":"Matt McKenna","picks":["Ludvig Åberg","Matt Fitzpatrick","Patrick Reed","Nicolai Højgaard","Adam Scott"]},
    {"name":"Maxwell","picks":["Xander Schauffele","Tommy Fleetwood","Justin Rose","Hideki Matsuyama","Sungjae Im"]},
    {"name":"Patrick Carroll","picks":["Justin Rose","Patrick Reed","Akshay Bhatia","Nicolai Højgaard","Jake Knapp"]},
    {"name":"Pete","picks":["Xander Schauffele","Matt Fitzpatrick","Cameron Young","Collin Morikawa","Sepp Straka"]},
    {"name":"Rob","picks":["Rory McIlroy","Ludvig Åberg","Xander Schauffele","Matt Fitzpatrick","Justin Rose"]},
    {"name":"Scott","picks":["Ludvig Åberg","Matt Fitzpatrick","Collin Morikawa","Robert MacIntyre","Jordan Spieth"]},
    {"name":"Tim","picks":["Xander Schauffele","Tommy Fleetwood","Robert MacIntyre","Hideki Matsuyama","Corey Conners"]},
    {"name":"Tom","picks":["Xander Schauffele","Robert MacIntyre","Patrick Reed","Hideki Matsuyama","Corey Conners"]}
]

NAME_MAP = {
    "Ludvig Aberg": "Ludvig Åberg",
    "Ludvig Åberg": "Ludvig Åberg",
    "Matthew Fitzpatrick": "Matt Fitzpatrick",
    "Nicolai Hojgaard": "Nicolai Højgaard",
    "Rasmus Hojgaard": "Rasmus Højgaard",
}

def normalize(name):
    return NAME_MAP.get(name, name)

def fetch_leaderboard():
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(ESPN_URL, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()

    events = data.get("events", [])
    if not events:
        raise RuntimeError("No events in ESPN response")

    competitors = events[0]["competitions"][0]["competitors"]

    # Sort by order field — this is the live leaderboard position
    competitors.sort(key=lambda x: x.get("order", 9999))

    # Assign tied positions: players with the same score share the same position
    leaderboard = []
    prev_score = None
    prev_position = 0
    rank = 0

    for c in competitors:
        score = c.get("score", "")
        name = normalize(c.get("athlete", {}).get("displayName", ""))
        if not name:
            continue

        rank += 1
        if score != prev_score:
            prev_position = rank
        prev_score = score

        leaderboard.append({"name": name, "position": prev_position})

    return leaderboard[:15]

def update_jsonbin(payload):
    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"
    headers = {
        "Content-Type": "application/json",
        "X-Master-Key": JSONBIN_MASTER_KEY
    }
    r = requests.put(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def main():
    print("Fetching ESPN leaderboard...")
    leaderboard = fetch_leaderboard()

    if not leaderboard:
        raise RuntimeError("No leaderboard data parsed from ESPN")

    print(f"Got {len(leaderboard)} players:")
    for row in leaderboard:
        print(f"  Pos {row['position']} — {row['name']}")

    payload = {
        "leaderboard": leaderboard,
        "participants": PARTICIPANTS,
        "lastUpdated": datetime.now(timezone.utc).strftime("%d %b %H:%M UTC"),
        "source": ESPN_URL
    }

    print("\nPushing to JSONBin...")
    update_jsonbin(payload)
    print(f"✅ Done — {len(leaderboard)} rows written to bin {JSONBIN_BIN_ID}")

if __name__ == "__main__":
    main()