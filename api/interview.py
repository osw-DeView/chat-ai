# api/interview.py

from fastapi import APIRouter

from models.interview_models import (
    InterviewStartRequest, InterviewStartResponse,
    InterviewNextRequest, InterviewNextResponse,
    InterviewEvaluationRequest, InterviewEvaluationResponse
)

from services.gemini_service import generate_tail_question, evaluate_conversation
from services.initial_questions import get_random_question

router = APIRouter(
    prefix="/interview",
    tags=["interview"]
)

@router.post("/start", response_model=InterviewStartResponse)
def start_interview(request: InterviewStartRequest): # async 제거
    """
    면접 유형(CS)을 받아 CSV 파일에서 읽어온 초기 질문 중 하나를 무작위로 반환합니다.
    """
    question = get_random_question()
    return InterviewStartResponse(response=question)


@router.post("/next", response_model=InterviewNextResponse)
async def get_next_question(request: InterviewNextRequest):
    """
    이전 대화 내용을 받아 Gemini API를 통해 다음 꼬리 질문을 비동기로 생성하고 성능을 반환합니다.
    """
    # 비동기 함수 호출이므로 await 추가
    result = await generate_tail_question(request.conversation)
    return InterviewNextResponse(response=result['response'], performance=result['performance'])


# --- 👇 3단계 수정의 핵심 변경 사항 ---

# api/interview.py
@router.post("/evaluation", response_model=InterviewEvaluationResponse)
async def evaluate_interview(request: InterviewEvaluationRequest):
    """
    전체 대화 내용을 받아 Gemini API를 통해 구조화된 종합 평가를 비동기로 생성합니다.
    (성능 지표는 내부적으로만 계산되고 클라이언트에게는 반환되지 않습니다.)
    """
    # 비동기 함수 호출이므로 await 추가
    evaluation_result = await evaluate_conversation(request.conversation)
    return InterviewEvaluationResponse(
        evaluation_report=evaluation_result['evaluation_report']
    )