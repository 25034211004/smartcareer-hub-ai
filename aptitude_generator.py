
import json
import re

from gemini_service import ask_gemini


ALLOWED_TOPICS = {
    "quantitative": "Quantitative Aptitude",
    "logical": "Logical Reasoning",
    "verbal": "Verbal Ability",
    "technical": "Technical Aptitude",
    "mixed": "Mixed Aptitude"
}

ALLOWED_DIFFICULTIES = {
    "easy": "Easy",
    "medium": "Medium",
    "hard": "Hard"
}


def parse_json_response(response_text):
    """
    Parse Gemini's JSON response.
    Also handle accidental Markdown code fences.
    """

    text = response_text.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(r"\s*```$", "", text)

    return json.loads(text)


def validate_questions(data, expected_count):
    """
    Validate generated questions before returning
    them to the PHP application.
    """

    if not isinstance(data, dict):
        raise ValueError("Invalid response format.")

    questions = data.get("questions")

    if not isinstance(questions, list):
        raise ValueError("Questions list is missing.")

    if len(questions) != expected_count:
        raise ValueError(
            "Gemini returned an incorrect question count."
        )

    validated = []

    for number, item in enumerate(questions, start=1):

        if not isinstance(item, dict):
            raise ValueError("Invalid question.")

        question = item.get("question")
        options = item.get("options")
        correct_index = item.get("correct_index")
        explanation = item.get("explanation")

        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question text is missing.")

        if (
            not isinstance(options, list)
            or len(options) != 4
            or not all(
                isinstance(option, str) and option.strip()
                for option in options
            )
        ):
            raise ValueError("Every question needs four options.")

        if (
            type(correct_index) is not int
            or correct_index not in [0, 1, 2, 3]
        ):
            raise ValueError("Invalid correct answer index.")

        if (
            not isinstance(explanation, str)
            or not explanation.strip()
        ):
            raise ValueError("Explanation is missing.")

        validated.append({
            "id": number,
            "question": question.strip(),
            "options": [option.strip() for option in options],
            "correct_index": correct_index,
            "explanation": explanation.strip()
        })

    return validated


def generate_aptitude_test(
    topic="quantitative",
    difficulty="medium",
    count=5
):
    """
    Generate an aptitude test using Gemini AI.
    """

    if topic not in ALLOWED_TOPICS:
        raise ValueError("Invalid aptitude topic.")

    if difficulty not in ALLOWED_DIFFICULTIES:
        raise ValueError("Invalid difficulty.")

    if type(count) is not int or count not in [5, 10]:
        raise ValueError("Question count must be 5 or 10.")

    topic_name = ALLOWED_TOPICS[topic]
    difficulty_name = ALLOWED_DIFFICULTIES[difficulty]

    prompt = f"""
You are an aptitude test question generator
for SmartCareer Hub, a student placement portal.

Generate exactly {count} multiple-choice questions.

Topic: {topic_name}
Difficulty: {difficulty_name}

Requirements:
- Questions should be suitable for campus placement preparation.
- Every question must have exactly four options.
- There must be exactly one correct answer.
- Use correct_index values 0, 1, 2 or 3.
- Provide a clear explanation for each answer.
- For quantitative questions, verify the arithmetic.
- Avoid duplicate questions.
- Do not include unsupported or ambiguous answers.
- For mixed aptitude, include a variety of topics.

Return ONLY valid JSON with this exact structure:

{{
  "questions": [
    {{
      "question": "Example question?",
      "options": [
        "Option A",
        "Option B",
        "Option C",
        "Option D"
      ],
      "correct_index": 0,
      "explanation": "Explanation of the correct answer."
    }}
  ]
}}

Do not include Markdown code fences.
Do not include text outside the JSON.
"""

    last_error = None

    # Retry if Gemini generates malformed questions.
    for attempt in range(2):
        try:
            response = ask_gemini(prompt)

            data = parse_json_response(response)

            questions = validate_questions(data, count)

            return {
                "topic": topic_name,
                "difficulty": difficulty_name,
                "total_questions": len(questions),
                "questions": questions
            }

        except (ValueError, json.JSONDecodeError) as error:
            last_error = error

    raise ValueError(
        "Could not generate a valid aptitude test."
    ) from last_error
