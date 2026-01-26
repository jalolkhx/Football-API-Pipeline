import requests
import pandas as pd
import os
from datetime import datetime

# =========================
# CONFIG
# =========================
API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
LEAGUE_ID = 39        # Premier League
#SEASON = datetime.now().year - 1 if datetime.now().month < 8 else datetime.now().year
SEASON = 2024
HEADERS = {
    "x-apisports-key": API_KEY
}

# =========================
# HELPERS
# =========================
def api_get(endpoint, params=None):
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()["response"]

# =========================
# 1. EPL STANDINGS
# =========================
def get_standings():
    data = api_get("/standings", {
        "league": LEAGUE_ID,
        "season": SEASON
    })

    table = data[0]["league"]["standings"][0]

    rows = []
    for t in table:
        rows.append({
            "rank": t["rank"],
            "team": t["team"]["name"],
            "points": t["points"],
            "played": t["all"]["played"],
            "wins": t["all"]["win"],
            "draws": t["all"]["draw"],
            "losses": t["all"]["lose"],
            "goals_for": t["all"]["goals"]["for"],
            "goals_against": t["all"]["goals"]["against"],
            "goal_difference": t["goalsDiff"]
        })

    return pd.DataFrame(rows)

# =========================
# 2. TOP SCORERS
# =========================
def get_top_scorers():
    data = api_get("/players/topscorers", {
        "league": LEAGUE_ID,
        "season": SEASON
    })

    rows = []
    for p in data:
        stats = p["statistics"][0]
        rows.append({
            "player": p["player"]["name"],
            "team": stats["team"]["name"],
            "goals": stats["goals"]["total"],
            "appearances": stats["games"]["appearences"]
        })

    return pd.DataFrame(rows)

# =========================
# 3. TOP ASSISTS
# =========================
def get_top_assists():
    data = api_get("/players/topassists", {
        "league": LEAGUE_ID,
        "season": SEASON
    })

    rows = []
    for p in data:
        stats = p["statistics"][0]
        rows.append({
            "player": p["player"]["name"],
            "team": stats["team"]["name"],
            "assists": stats["goals"]["assists"],
            "appearances": stats["games"]["appearences"]
        })

    return pd.DataFrame(rows)