import os
import time
import logging

import mysql.connector

from google import genai
from google.genai import errors


# =========================================================
# DATABASE CONFIGURATION
# Render Environment Variables
# =========================================================

DB_CONFIG = {
    "host": os.environ.get("DB_HOST"),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "database": os.environ.get("DB_NAME"),
    "port": int(os.environ.get("DB_PORT", "3306"))
}


# =========================================================
# GET GEMINI API KEY FROM ADMIN SETTINGS
# =========================================================

def get_gemini_api_key():

    connection = None
    cursor = None

    try:

        connection = mysql.connector.connect(
            **DB_CONFIG
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT setting_value
            FROM ai_settings
            WHERE setting_name = %s
            LIMIT 1
            """,
            ("gemini_api_key",)
        )

        row = cursor.fetchone()

        if not row:
            raise RuntimeError(
                "Gemini API Key is not configured. "
                "Please configure it from "
                "Admin > AI Settings."
            )

        api_key = str(row[0]).strip()

        if not api_key:
            raise RuntimeError(
                "Gemini API Key is not configured. "
                "Please configure it from "
                "Admin > AI Settings."
            )

        return api_key

    except mysql.connector.Error as e:

        logging.error(
            "Database error while reading Gemini API key: %s",
            e
        )

        raise RuntimeError(
            "Unable to read Gemini API Key "
            "from the database."
        ) from e

    finally:

        if cursor is not None:
            cursor.close()

        if (
            connection is not None
            and connection.is_connected()
        ):
            connection.close()


# =========================================================
# GEMINI MODELS
# =========================================================

MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash"
]


# =========================================================
# ASK GEMINI
# =========================================================

def ask_gemini(question):

    # Gemini API key is fetched from Admin > AI Settings
    api_key = get_gemini_api_key()

    client = genai.Client(
        api_key=api_key
    )

    last_error = None

    for model in MODELS:

        for attempt in range(2):

            try:

                print(
                    f"Trying model: {model}"
                )

                response = (
                    client.models.generate_content(
                        model=model,
                        contents=question
                    )
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

                # Model unavailable -> try next model
                if e.code == 404:

                    logging.warning(
                        "%s is unavailable. Trying fallback.",
                        model
                    )

                    break

                raise

    if last_error:
        raise last_error

    raise RuntimeError(
        "No Gemini model returned a response."
    )
