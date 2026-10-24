
import os
import time
import logging

from google import genai
from google.genai import errors


# =========================================================
# CONFIGURATION
# =========================================================

# Keep request timeout limited so PHP does not wait indefinitely.
GEMINI_TIMEOUT_MS = 25000

# Limited retry attempts for temporary errors.
MAX_RETRIES = 2

# Use only model IDs supported by your Gemini API account.
MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
]

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


# =========================================================
# API KEY
# =========================================================

def get_gemini_api_key():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing in Render Environment Variables."
        )

    return api_key


# =========================================================
# GEMINI SERVICE
# =========================================================

def ask_gemini(question):

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Gemini question cannot be empty.")

    api_key = get_gemini_api_key()

    client = genai.Client(
        api_key=api_key,
        http_options={
            "timeout": GEMINI_TIMEOUT_MS
        }
    )

    last_error = None

    for model in MODELS:

        for attempt in range(MAX_RETRIES + 1):

            try:
                logging.info(
                    "Trying Gemini model %s, attempt %s/%s",
                    model,
                    attempt + 1,
                    MAX_RETRIES + 1
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
                    "Gemini returned an empty response."
                )

            except errors.ServerError as error:
                last_error = error
                status = getattr(error, "code", None)

                if status not in RETRYABLE_STATUS_CODES:
                    logging.exception(
                        "Non-retryable Gemini server error on %s",
                        model
                    )
                    raise

                logging.warning(
                    "Gemini temporary server error %s on %s, attempt %s",
                    status,
                    model,
                    attempt + 1
                )

                if attempt < MAX_RETRIES:
                    time.sleep(1 if attempt == 0 else 2)
                    continue

                # Move to the next configured model.
                break

            except errors.ClientError as error:
                last_error = error
                status = getattr(error, "code", None)

                if status == 404:
                    logging.warning(
                        "Gemini model %s not found; trying fallback.",
                        model
                    )
                    break

                if status == 429:
                    logging.warning(
                        "Gemini rate limit reached on %s.",
                        model
                    )

                    if attempt < MAX_RETRIES:
                        time.sleep(1 if attempt == 0 else 2)
                        continue

                    break

                # Invalid key, permission errors, etc. should not
                # be retried across every model.
                logging.exception(
                    "Gemini client error on model %s",
                    model
                )
                raise

            except Exception as error:
                last_error = error

                logging.exception(
                    "Gemini request failed on model %s",
                    model
                )

                # Do not retry unknown errors automatically.
                raise

    if last_error is not None:
        raise last_error

    raise RuntimeError(
        "No configured Gemini model returned a response."
    )
