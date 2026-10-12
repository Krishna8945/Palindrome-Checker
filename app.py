"""
Palindrome Checker Web Application
Powered by Python Flask and collections.deque (Double-Ended Queue)
"""

from flask import Flask, render_template, request, jsonify
from collections import deque
import re
import string

app = Flask(__name__)


def check_palindrome_deque(raw_text: str, ignore_case: bool = True, 
                           ignore_spaces: bool = True, ignore_punctuation: bool = True):
    """
    Checks whether a given string is a palindrome using a Double-Ended Queue (deque).
    
    Why collections.deque?
    In Python, collections.deque provides O(1) time complexity for popping from both ends 
    (popleft() and pop()), whereas a standard Python list takes O(n) for pop(0) due to 
    element shifting. This makes deque the ideal data structure for two-pointer / two-ended 
    verification algorithms.
    """
    if raw_text is None:
        raw_text = ""

    # Process and clean the text according to selected options
    cleaned_chars = []
    for char in raw_text:
        # Check punctuation
        if ignore_punctuation and (char in string.punctuation or char in "“”‘’—–…"):
            continue
        # Check whitespace
        if ignore_spaces and char.isspace():
            continue
        # Casing
        if ignore_case:
            char = char.lower()
        cleaned_chars.append(char)

    cleaned_text = "".join(cleaned_chars)

    if not cleaned_text:
        return {
            "is_empty": True,
            "raw_text": raw_text,
            "cleaned_text": "",
            "is_palindrome": False,
            "message": "Input contains no evaluable characters under the current filter settings.",
            "steps": [],
            "total_chars": 0,
            "middle_char": None,
            "options": {
                "ignore_case": ignore_case,
                "ignore_spaces": ignore_spaces,
                "ignore_punctuation": ignore_punctuation
            }
        }

    # Initialize double-ended queue
    char_deque = deque(cleaned_chars)
    initial_deque_state = list(char_deque)

    steps = []
    is_palindrome = True
    step_num = 1

    # Compare characters by popping simultaneously from front and rear
    while len(char_deque) > 1:
        front_char = char_deque.popleft()
        rear_char = char_deque.pop()
        matched = (front_char == rear_char)

        steps.append({
            "step": step_num,
            "front": front_char,
            "rear": rear_char,
            "matched": matched,
            "remaining_deque": list(char_deque),
            "remaining_str": "".join(char_deque)
        })

        if not matched:
            is_palindrome = False
            break

        step_num += 1

    # If length was odd and it is a palindrome, the middle character remains in deque
    middle_char = char_deque[0] if (len(char_deque) == 1 and is_palindrome) else None

    return {
        "is_empty": False,
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
        "initial_deque": initial_deque_state,
        "is_palindrome": is_palindrome,
        "message": "Congratulations! It's a valid palindrome." if is_palindrome else "Not a palindrome. Characters did not match.",
        "steps": steps,
        "total_chars": len(cleaned_text),
        "middle_char": middle_char,
        "options": {
            "ignore_case": ignore_case,
            "ignore_spaces": ignore_spaces,
            "ignore_punctuation": ignore_punctuation
        }
    }


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    input_text = ""
    ignore_case = True
    ignore_spaces = True
    ignore_punctuation = True

    if request.method == "POST":
        input_text = request.form.get("text", "")
        ignore_case = "ignore_case" in request.form
        ignore_spaces = "ignore_spaces" in request.form
        ignore_punctuation = "ignore_punctuation" in request.form

        if input_text.strip():
            result = check_palindrome_deque(
                input_text,
                ignore_case=ignore_case,
                ignore_spaces=ignore_spaces,
                ignore_punctuation=ignore_punctuation
            )
        else:
            result = {
                "is_empty": True,
                "raw_text": "",
                "cleaned_text": "",
                "is_palindrome": False,
                "message": "Please enter a word or sentence to check.",
                "steps": [],
                "total_chars": 0,
                "middle_char": None,
                "options": {
                    "ignore_case": ignore_case,
                    "ignore_spaces": ignore_spaces,
                    "ignore_punctuation": ignore_punctuation
                }
            }

    return render_template(
        "index.html",
        result=result,
        input_text=input_text,
        ignore_case=ignore_case,
        ignore_spaces=ignore_spaces,
        ignore_punctuation=ignore_punctuation
    )


@app.route("/api/check", methods=["POST"])
def api_check():
    """
    JSON API endpoint for real-time / AJAX palindrome verification.
    """
    data = request.get_json(silent=True) or request.form

    raw_text = data.get("text", "")
    ignore_case = data.get("ignore_case", True)
    ignore_spaces = data.get("ignore_spaces", True)
    ignore_punctuation = data.get("ignore_punctuation", True)

    # Cast boolean strings from JSON or form if needed
    if isinstance(ignore_case, str):
        ignore_case = ignore_case.lower() in ("true", "1", "on", "yes")
    if isinstance(ignore_spaces, str):
        ignore_spaces = ignore_spaces.lower() in ("true", "1", "on", "yes")
    if isinstance(ignore_punctuation, str):
        ignore_punctuation = ignore_punctuation.lower() in ("true", "1", "on", "yes")

    result = check_palindrome_deque(
        raw_text,
        ignore_case=bool(ignore_case),
        ignore_spaces=bool(ignore_spaces),
        ignore_punctuation=bool(ignore_punctuation)
    )

    return jsonify(result)


if __name__ == "__main__":
    print("Starting Palindrome Checker Flask App on http://127.0.0.1:5000")
    app.run(debug=True, host="127.0.0.1", port=5000)
