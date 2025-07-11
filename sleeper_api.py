import requests

BASE = "https://api.sleeper.app/v1"


def get_user(username_or_id):
    res = requests.get(f"{BASE}/user/{username_or_id}")
    return res.json()


def get_league(league_id):
    res = requests.get(f"{BASE}/league/{league_id}")
    return res.json()


def get_leagues(user_id, season="2024"):
    res = requests.get(f"{BASE}/user/{user_id}/leagues/nfl/{season}")
    return res.json()


def get_roster(league_id):
    res = requests.get(f"{BASE}/league/{league_id}/rosters")
    return res.json()


def get_users_in_league(league_id):
    res = requests.get(f"{BASE}/league/{league_id}/users")
    return res.json()


def get_matchups(league_id, week):
    res = requests.get(f"{BASE}/league/{league_id}/matchups/{week}")
    return res.json()


def get_standings(league_id):
    rosters = get_roster(league_id)
    return sorted(
        rosters, key=lambda r: (-r["settings"]["wins"], r["settings"]["losses"])
    )


def get_players():
    res = requests.get(f"{BASE}/players/nfl")
    return res.json()
