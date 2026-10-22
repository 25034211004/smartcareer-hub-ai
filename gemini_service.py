
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
# GEMINI MODELS
# =========================================================

MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash"
]

# =========================================================
# ASK GEMINI
# =========================================================

def ask_gemini(question):

    api_key = get_gemini_api_key()

    client = genai.Client(api_key=api_key)

    last_error = None

    for model in MODELS:

        for attempt in range(2):

            try:
                logging.info("Trying Gemini model: %s", model)

                response = client.models.generate_content(
                    model=model,
                    contents=question
                )

                if response.text:
                    return response.text

                raise RuntimeError(
                    f"{model} returned an empty response."
                )

            except errors.ServerError as e:
                last_error = e

                if e.code == 503:
                    logging.warning(
                        "%s is busy. Attempt %s",
                        model,
                        attempt + 1
                    )

                    if attempt == 0:
                        time.sleep(3)
                        continue

                    break

                raise

            except errors.ClientError as e:
                last_error = e

                if e.code == 404:
                    logging.warning(
                        "%s is unavailable. Trying fallback model.",
                        model
                    )
                    break

                raise

    if last_error:
        raise last_error

    raise RuntimeError(
        "No Gemini model returned a response."
    )
