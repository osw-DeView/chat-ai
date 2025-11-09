import random
from fastapi import APIRouter

from models.interview_models import (
    InterviewStartRequest, InterviewStartResponse,
    InterviewNextRequest, InterviewNextResponse,
    InterviewEvaluationRequest, InterviewEvaluationResponse
)

from services.gemini_service import generate_tail_question, evaluate_conversation
from services.initial_questions import INITIAL_CS_QUESTIONS

router = APIRouter(
    prefix="/interview",
    tags=["interview"]
)

@router.post("/start", response_model=InterviewStartResponse)
async def start_interview(request: InterviewStartRequest):
    """
    면접 유형(CS)을 받아 미리 정의된 초기 질문 중 하나를 무작위로 반환합니다.
    """
    question = random.choice(INITIAL_CS_QUESTIONS)
    return InterviewStartResponse(response=question)


@router.post("/next", response_model=InterviewNextResponse)
async def get_next_question(request: InterviewNextRequest):
    """
    이전 대화 내용을 받아 Gemini API를 통해 다음 꼬리 질문을 생성합니다.
    """
    tail_question = generate_tail_question(request.conversation)
    return InterviewNextResponse(response=tail_question)


@router.post("/evaluation", response_model=InterviewEvaluationResponse)
async def evaluate_interview(request: InterviewEvaluationRequest):
    """
    전체 대화 내용을 받아 Gemini API를 통해 종합적인 평가를 생성합니다.
    """
    evaluation_result = evaluate_conversation(request.conversation)
    return InterviewEvaluationResponse(**evaluation_result)