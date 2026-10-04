
import os
import json
import urllib.request
import urllib.error


GEMINI_API_KEY = os.environ.get(
    "GEMINI_API_KEY", ""
)

GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)


def fallback_notifications(student):
    """
    Useful reminders when Gemini is unavailable.
    """

    skills = student.get("skills", "")
    target_role = student.get(
        "target_role", ""
    )

    notifications = []

    if target_role:
        notifications.append(
            f"Career Tip: Review the skills required "
            f"for {target_role} and complete one "
            f"practical project this week."
        )
    else:
        notifications.append(
            "Career Tip: Select your preferred job "
            "role and prepare a weekly learning plan."
        )

    if skills:
        notifications.append(
            "Resume Tip: Highlight your experience "
            "with your technical skills and add "
            "measurable project achievements."
        )
    else:
        notifications.append(
            "Profile Reminder: Add your technical "
            "skills to improve your career profile."
        )

    notifications.append(
        "Aptitude Reminder: Practice quantitative "
        "aptitude, logical reasoning and verbal "
        "questions for your placement preparation."
    )

    return notifications


def generate_ai_notifications(student):
    """
    Generate personalized notifications
    using Gemini API.
    """

    if not GEMINI_API_KEY:
        return fallback_notifications(student)

    prompt = f"""
You are the AI career assistant for SmartCareer Hub,
a student placement and job recommendation website.

Student data:
{json.dumps(student, ensure_ascii=False)}

Generate exactly three personalized notifications.

Topics:
1. Career preparation or relevant job-search advice.
2. Resume or technical skill improvement.
3. Aptitude or interview preparation.

Rules:
- Each message must be concise.
- Maximum 220 characters per message.
- Give practical, actionable advice.
- Do not invent available jobs.
- Do not invent hiring probabilities.
- Do not promise that the student will be hired.
- Avoid repeating the same advice.
- Return only a JSON array containing 3 strings.
"""

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        + GEMINI_MODEL
        + ":generateContent"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "responseMimeType": "application/json"
        }
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(
            payload
        ).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        },
        method="POST"
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=45
        ) as response:

            api_response = json.loads(
                response.read().decode("utf-8")
            )

        generated_text = (
            api_response["candidates"][0]
            ["content"]["parts"][0]["text"]
        )

        notifications = json.loads(
            generated_text
        )

        if not isinstance(
            notifications, list
        ):
            raise ValueError(
                "AI response must be a list."
            )

        cleaned = []

        for message in notifications:

            if not isinstance(
                message, str
            ):
                continue

            message = message.strip()

            if message:
                cleaned.append(
                    message[:220]
                )

        if len(cleaned) != 3:
            raise ValueError(
                "AI must return 3 notifications."
            )

        return cleaned

    except Exception as error:

        print(
            "Gemini notification error:",
            error
        )

        return fallback_notifications(
            student
        )
