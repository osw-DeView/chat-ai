import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

TAIL_QUESTION_MODEL = os.getenv("TAIL_QUESTION_MODEL", "gemini-2.5-flash-lite")

EVALUATION_MODEL = os.getenv("EVALUATION_MODEL", "gemini-2.5-flash")