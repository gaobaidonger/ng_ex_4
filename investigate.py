import json
import os
import ollama

from parse_data import (
    load_items,
    get_unclaimed_items,
    save_result
)


def build_prompt(description, available_items):
    system_prompt = """
You are a campus lost-and-found matching assistant.

You must follow these rules exactly:

1. Use only the items provided in the JSON data.
2. An item can be a possible match even if not every detail matches.
3. Return only valid JSON.
4. Do not include markdown or explanations.
5. Return exactly this structure:

{
    "matches": ["ITEM_ID"],
    "confidence": "LOW"
}

6. "matches" must contain all possible matching item IDs.
7. "confidence" must be exactly one of:
   LOW, MEDIUM, HIGH.
8. If there is no possible match, return an empty list.
9. Never invent an item ID that is not in the provided data.
"""

    items_json = json.dumps(
        available_items,
        ensure_ascii=False,
        indent=2
    )

    user_prompt = f"""
Lost item description:

{description}

Available unclaimed items:

{items_json}

Find all possible matches and return only the required JSON object.
"""

    return system_prompt, user_prompt


def ask_qwen(system_prompt, user_prompt):
    model_name = os.getenv(
        "QWEN_MODEL",
        "qwen3:8b"
    )

    response = ollama.chat(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        format="json"
    )

    try:
        return response["message"]["content"]

    except (TypeError, KeyError):
        return response.message.content


def parse_response(response_text):
    text = response_text.strip()

    # In case Qwen accidentally returns a markdown code block
    if text.startswith("```"):
        lines = text.splitlines()

        lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    return json.loads(text)


def validate_result(result, available_items):
    if not isinstance(result, dict):
        return False

    if "matches" not in result:
        return False

    if "confidence" not in result:
        return False

    matches = result["matches"]
    confidence = result["confidence"]

    if not isinstance(matches, list):
        return False

    if not all(
        isinstance(item_id, str)
        for item_id in matches
    ):
        return False

    if not isinstance(confidence, str):
        return False

    if confidence not in {
        "LOW",
        "MEDIUM",
        "HIGH"
    }:
        return False

    valid_ids = {
        item["id"]
        for item in available_items
        if "id" in item
    }

    for item_id in matches:
        if item_id not in valid_ids:
            return False

    return True


def display_matches(result, available_items):
    print("\nMATCH RESULT")
    print("-" * 50)

    print(
        f"Confidence: {result['confidence']}"
    )

    print("\nPossible matches:")

    matches = result["matches"]

    if not matches:
        print("No matches found.")
        print("[]")
        return

    items_by_id = {
        item["id"]: item
        for item in available_items
    }

    for item_id in matches:
        item = items_by_id[item_id]

        print()

        print(
            f"ID: {item['id']}"
        )

        print(
            f"Item: {item['item']}"
        )

        print(
            f"Color: {item['color']}"
        )

        print(
            f"Location: {item['location']}"
        )

        print(
            f"Date found: {item['date']}"
        )


def main():
    print(
        "CAMPUS LOST-AND-FOUND ASSISTANT"
    )

    print("=" * 50)

    description = input(
        "\nDescribe the item you lost: "
    ).strip()

    items = load_items(
        "found_items.json"
    )

    available_items = get_unclaimed_items(
        items
    )

    system_prompt, user_prompt = build_prompt(
        description,
        available_items
    )

    print(
        "\nSearching for possible matches..."
    )

    response_text = ask_qwen(
        system_prompt,
        user_prompt
    )

    result = parse_response(
        response_text
    )

    if not validate_result(
        result,
        available_items
    ):
        raise ValueError(
            "Qwen returned an invalid result."
        )

    display_matches(
        result,
        available_items
    )

    output_file = (
        "output/match_result.json"
    )

    save_result(
        result,
        output_file
    )

    print(
        f"\nResult saved to {output_file}"
    )


if __name__ == "__main__":
    main()