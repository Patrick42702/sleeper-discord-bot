import glob
import json
import os


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
        abs_path = os.path.abspath(files[0])
        return f"file://{abs_path}"
    return None
