import json
import os


def load_items(filename):
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data["items"]


def get_unclaimed_items(items):
    return [
        item
        for item in items
        if item.get("status", "").strip().lower() == "unclaimed"
    ]


def save_result(result, filename):
    directory = os.path.dirname(str(filename))

    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(
            result,
            file,
            indent=4,
            ensure_ascii=False
        )