import mimetypes
import os

import requests

BASE = "https://api.sleeper.app/v1"
AVATAR_CDN = "https://sleepercdn.com/avatars"

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

def get_avatars(league_id):
    users = get_users_in_league(league_id)
    os.makedirs("avatars", exist_ok=True)

    avatar_filenames = []

    for user in users:
        metadata = user.get("metadata")
        avatar_url = ""
        avatar_id = user.get("avatar")
        user_id = user.get("user_id")
        if "avatar" in metadata: # If the user has a league specific avatar
            avatar_url = metadata["avatar"]
            try:
                res = requests.get(avatar_url)
                res.raise_for_status()

                content_type = res.headers.get("Content-Type", "").lower()
                ext = mimetypes.guess_extension(content_type)
                if ext == ".bin":
                    ext = ".png"
                filename = f"{user_id}{ext}"
                file_path = os.path.join("avatars", filename)
                with open(file_path, "wb") as f:
                    f.write(res.content)
                avatar_filenames.append(filename)
            except requests.RequestException as e:
                print(f"Failed to download avatar {avatar_id}: {e}")
        else:
            avatar_url = f"{AVATAR_CDN}/{avatar_id}"
            try:
                res = requests.get(avatar_url)
                res.raise_for_status()

                # Detect content type (e.g., image/jpeg)
                content_type = res.headers.get("Content-Type", "").lower()
                ext = mimetypes.guess_extension(content_type)

                # Fallback to .webp if unknown
                if ext == ".bin":
                    ext = ".png"

                filename = f"{user_id}{ext}"
                file_path = os.path.join("avatars", filename)
                with open(file_path, "wb") as f:
                    f.write(res.content)

                avatar_filenames.append(filename)
            except requests.RequestException as e:
                print(f"Failed to download avatar {avatar_id}: {e}")

    return avatar_filenames


def get_players():
    res = requests.get(f"{BASE}/players/nfl")
    return res.json()
