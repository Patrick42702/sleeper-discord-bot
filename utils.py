import glob
import json
import os
from pathlib import Path


def load_json(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f)
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def find_avatar_path(user_id):
    files = glob.glob(f"avatars/{user_id}.*")
    if files:
        abs_path = Path(files[0]).resolve()
        return abs_path.as_uri()  # gives valid file:// URI on any OS
    return None
