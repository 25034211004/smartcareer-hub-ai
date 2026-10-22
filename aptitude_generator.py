
import json
import re
import logging

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
    text = response_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def validate_questions(data, expected_count):
    if not isinstance(data, dict):
        raise ValueError("Invalid response format.")

    questions = data.get("questions")

    if not isinstance(questions, list):
        raise ValueError("Questions list is missing.")

    if len(questions) != expected_count:
        raise ValueError("Incorrect question count.")

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
            or not all(isinstance(x, str) and x.strip() for x in options)
        ):
            raise ValueError("Each question needs four options.")

        if type(correct_index) is not int or correct_index not in range(4):
            raise ValueError("Invalid correct answer index.")

        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError("Explanation is missing.")

        validated.append({
            "id": number,
            "question": question.strip(),
            "options": [x.strip() for x in options],
            "correct_index": correct_index,
            "explanation": explanation.strip()
        })

    return validated


def make_question(question, options, answer, explanation):
    return {
        "question": question,
        "options": options,
        "correct_index": answer,
        "explanation": explanation
    }


def generate_local_questions(topic, difficulty, count):
    """
    Reliable local fallback. Does not call Gemini.
    """

    banks = {
        "quantitative": [
            make_question("What is 15% of 200?",
                          ["20", "30", "40", "50"], 1,
                          "15% of 200 = 15/100 × 200 = 30."),
            make_question("If 5x = 45, what is x?",
                          ["5", "8", "9", "10"], 2,
                          "Divide both sides by 5: x = 45/5 = 9."),
            make_question("What is the average of 10, 20 and 30?",
                          ["15", "20", "25", "30"], 1,
                          "Average = (10 + 20 + 30) / 3 = 20."),
            make_question("A product costs 500 rupees. Its price increases by 10%. What is the new price?",
                          ["510", "525", "550", "600"], 2,
                          "10% of 500 is 50, so the new price is 550."),
            make_question("What is 3/4 expressed as a percentage?",
                          ["25%", "50%", "75%", "80%"], 2,
                          "3/4 × 100 = 75%."),
            make_question("A car travels 120 km in 2 hours. What is its average speed?",
                          ["40 km/h", "50 km/h", "60 km/h", "80 km/h"], 2,
                          "Speed = distance / time = 120 / 2 = 60 km/h."),
            make_question("What is the simple interest on 1000 rupees at 5% per year for 2 years?",
                          ["50", "100", "150", "200"], 1,
                          "Simple interest = P × R × T / 100 = 100."),
            make_question("What is 12 × 8?",
                          ["84", "88", "96", "108"], 2,
                          "12 multiplied by 8 equals 96."),
            make_question("If a dozen pens costs 120 rupees, what is the cost of one pen?",
                          ["5", "10", "12", "20"], 1,
                          "120 divided by 12 equals 10 rupees."),
            make_question("What is the square of 13?",
                          ["156", "159", "169", "179"], 2,
                          "13 × 13 = 169.")
        ],

        "logical": [
            make_question("Find the next number: 2, 4, 6, 8, ?",
                          ["9", "10", "11", "12"], 1,
                          "Each number increases by 2."),
            make_question("Find the next number: 3, 6, 12, 24, ?",
                          ["30", "36", "48", "60"], 2,
                          "Each number is multiplied by 2."),
            make_question("Which one is different?",
                          ["Apple", "Mango", "Carrot", "Banana"], 2,
                          "Carrot is commonly classified as a vegetable; the others are fruits."),
            make_question("If all roses are flowers, which statement must be true?",
                          ["All flowers are roses", "Roses are flowers", "No roses are flowers", "All plants are roses"], 1,
                          "The given statement directly says roses are flowers."),
            make_question("Find the next letter: A, C, E, G, ?",
                          ["H", "I", "J", "K"], 1,
                          "The sequence skips one letter each time."),
            make_question("Find the next number: 5, 10, 15, 20, ?",
                          ["22", "24", "25", "30"], 2,
                          "Each term increases by 5."),
            make_question("Which number does not belong?",
                          ["4", "9", "16", "20"], 3,
                          "4, 9 and 16 are perfect squares; 20 is not."),
            make_question("If today is Monday, what day will it be in 3 days?",
                          ["Tuesday", "Wednesday", "Thursday", "Friday"], 2,
                          "Three days after Monday is Thursday."),
            make_question("Find the next number: 1, 4, 9, 16, ?",
                          ["20", "24", "25", "36"], 2,
                          "These are squares: 1², 2², 3², 4², then 5² = 25."),
            make_question("Book is to reading as fork is to what?",
                          ["Writing", "Eating", "Sleeping", "Running"], 1,
                          "A book is used for reading; a fork is used for eating.")
        ],

        "verbal": [
            make_question("Choose the correct sentence.",
                          ["She go to school.", "She goes to school.", "She going school.", "She gone to school."], 1,
                          "With 'she' in the simple present, use 'goes'."),
            make_question("Choose the synonym of 'rapid'.",
                          ["Slow", "Fast", "Weak", "Quiet"], 1,
                          "Rapid means fast or quick."),
            make_question("Choose the antonym of 'ancient'.",
                          ["Old", "Historic", "Modern", "Past"], 2,
                          "Modern is the opposite of ancient."),
            make_question("Fill in the blank: He ___ playing cricket.",
                          ["am", "are", "is", "be"], 2,
                          "'He is playing' is the correct present continuous form."),
            make_question("What is the plural of 'child'?",
                          ["Childs", "Childes", "Children", "Childrens"], 2,
                          "The standard plural of child is children."),
            make_question("Choose the correctly spelled word.",
                          ["Necessary", "Necesary", "Neccessary", "Necessery"], 0,
                          "The correct spelling is necessary."),
            make_question("Fill in the blank: I have lived here ___ 2020.",
                          ["for", "since", "at", "by"], 1,
                          "'Since' is used with a starting point in time."),
            make_question("Choose the synonym of 'begin'.",
                          ["Finish", "Start", "Close", "Stop"], 1,
                          "Begin means start."),
            make_question("Choose the correct article: She ate ___ apple.",
                          ["a", "an", "thee", "no article ever"], 1,
                          "'An' is used before a vowel sound, as in apple."),
            make_question("Choose the antonym of 'generous'.",
                          ["Kind", "Helpful", "Stingy", "Friendly"], 2,
                          "Stingy is the opposite of generous.")
        ],

        "technical": [
            make_question("Which language is commonly used to structure web pages?",
                          ["HTML", "SQL", "C", "Bash"], 0,
                          "HTML defines the structure of web pages."),
            make_question("Which data structure follows FIFO?",
                          ["Stack", "Queue", "Tree", "Graph"], 1,
                          "A queue follows First In, First Out."),
            make_question("Which SQL command retrieves data?",
                          ["DELETE", "UPDATE", "SELECT", "DROP"], 2,
                          "SELECT retrieves records from a database."),
            make_question("Which of these is a Python list?",
                          ["(1, 2)", "{1: 2}", "[1, 2]", "<1, 2>"], 2,
                          "Square brackets create a Python list."),
            make_question("What does CPU stand for?",
                          ["Central Processing Unit", "Computer Personal Unit", "Central Program Utility", "Control Processing User"], 0,
                          "CPU stands for Central Processing Unit."),
            make_question("Which protocol is commonly used to load secure websites?",
                          ["FTP only", "HTTPS", "SMTP", "Telnet"], 1,
                          "HTTPS secures web communication using encryption."),
            make_question("Which keyword defines a function in Python?",
                          ["func", "define", "def", "function"], 2,
                          "Python functions are declared using def."),
            make_question("Which structure stores key-value pairs in Python?",
                          ["List", "Tuple", "Dictionary", "String"], 2,
                          "A Python dictionary stores key-value pairs."),
            make_question("What does DBMS stand for?",
                          ["Database Management System", "Data Backup Memory Service", "Digital Base Machine Setup", "Database Main Storage"], 0,
                          "DBMS stands for Database Management System."),
            make_question("Which operator checks equality in Python?",
                          ["=", "==", "!=", ":="], 1,
                          "The == operator compares values for equality.")
        ]
    }

    if topic == "mixed":
        pool = (
            banks["quantitative"]
            + banks["logical"]
            + banks["verbal"]
            + banks["technical"]
        )
    else:
        pool = banks[topic]

    # Select questions deterministically and avoid duplicates.
    questions = []
    for i in range(count):
        item = pool[i % len(pool)].copy()
        questions.append(item)

    # Hard mode changes the displayed test label, not question validity.
    return questions


def generate_aptitude_test(
    topic="quantitative",
    difficulty="medium",
    count=5
):
    if topic not in ALLOWED_TOPICS:
        raise ValueError("Invalid aptitude topic.")

    if difficulty not in ALLOWED_DIFFICULTIES:
        raise ValueError("Invalid difficulty.")

    if type(count) is not int or count not in (5, 10):
        raise ValueError("Question count must be 5 or 10.")

    topic_name = ALLOWED_TOPICS[topic]
    difficulty_name = ALLOWED_DIFFICULTIES[difficulty]

    prompt = f"""
You generate aptitude tests for SmartCareer Hub.

Generate exactly {count} multiple-choice questions.
Topic: {topic_name}
Difficulty: {difficulty_name}

Each question must have four options, one correct answer,
a correct_index from 0 to 3, and a clear explanation.
Verify all answers.

Return ONLY valid JSON in this format:
{{
  "questions": [
    {{
      "question": "Question text?",
      "options": ["A", "B", "C", "D"],
      "correct_index": 0,
      "explanation": "Explanation."
    }}
  ]
}}
Do not include Markdown or extra text.
"""

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

    except Exception as error:
        logging.warning(
            "Gemini aptitude generation failed; using local questions: %s",
            type(error).__name__
        )

        questions = generate_local_questions(topic, difficulty, count)
        questions = validate_questions(
            {"questions": questions},
            count
        )

        return {
            "topic": topic_name,
            "difficulty": difficulty_name,
            "total_questions": len(questions),
            "questions": questions,
            "fallback_used": True
        }
