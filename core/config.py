import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 꼬리 질문 생성에 사용할 모델을 지정합니다. (기본값: gemini-1.5-flash)
# Docker 환경 변수 또는 .env 파일을 통해 설정 가능합니다.
TAIL_QUESTION_MODEL = os.getenv("TAIL_QUESTION_MODEL", "gemini-2.5-flash-lite")

# 최종 평가에 사용할 모델을 지정합니다. (기본값: gemini-1.5-flash)
# Docker 환경 변수 또는 .env 파일을 통해 설정 가능합니다.
EVALUATION_MODEL = os.getenv("EVALUATION_MODEL", "gemini-2.5-flash")