
import os
import time
import logging

from google import genai
from google.genai import errors


# =========================================================
# GEMINI API KEY FROM RENDER ENVIRONMENT VARIABLES
# =========================================================

def get_gemini_api_key():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing in Render Environment Variables."
        )

    return api_key


# =========================================================
# GEMINI MODEL FALLBACK
# =========================================================
# If a model is unavailable, the next model is attempted.
# Model availability depends on your Gemini API access.
# =========================================================

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash"
]


# =========================================================
# ASK GEMINI WITH RETRIES
# =========================================================

def ask_gemini(question):

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Gemini question cannot be empty.")

    api_key = get_gemini_api_key()
    client = genai.Client(api_key=api_key)

    last_error = None

    for model in MODELS:

        # Up to 3 attempts for temporary server/rate-limit errors
        for attempt in range(3):

            try:
                logging.info(
                    "Trying Gemini model %s, attempt %s",
                    model,
                    attempt + 1
                )

                response = client.models.generate_content(
                    model=model,
                    contents=question
                )

                answer = getattr(response, "text", None)

                if isinstance(answer, str) and answer.strip():
                    logging.info(
                        "Gemini response received from %s",
                        model
                    )
                    return answer.strip()

                raise RuntimeError(
                    f"{model} returned an empty response."
                )

            except errors.ServerError as error:
                last_error = error
                status = getattr(error, "code", None)

                # Temporary server errors: retry with backoff
                if status in (429, 500, 502, 503, 504):
                    logging.warning(
                        "Gemini temporary error %s on %s, attempt %s",
                        status,
                        model,
                        attempt + 1
                    )

                    if attempt < 2:
                        time.sleep(2 ** (attempt + 1))
                        continue

                    break

                raise

            except errors.ClientError as error:
                last_error = error
                status = getattr(error, "code", None)

                if status == 404:
                    logging.warning(
                        "Gemini model %s unavailable; trying fallback.",
                        model
                    )
                    break

                # Invalid key, permissions, and other client errors
                # should be visible in logs instead of being hidden.
                raise

            except Exception:
                # Do not hide unexpected errors.
                logging.exception(
                    "Unexpected Gemini error using model %s",
                    model
                )
                raise

    if last_error is not None:
        raise last_error

    raise RuntimeError("No Gemini model returned a response.")
