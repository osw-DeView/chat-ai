from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
import logging

from models.interview_models import (
    InterviewStartRequest, InterviewStartResponse,
    InterviewNextRequest, InterviewNextResponse,
    InterviewEvaluationRequest, InterviewEvaluationResponse
)
from services.inference import interview_model
from services.initial_questions import get_random_question
from core import config

router = APIRouter(
    prefix="/interview",
    tags=["Interview API"]
)

logger = logging.getLogger("uvicorn")

@router.post("/start", response_model=InterviewStartResponse, summary="면접 시작 및 초기 질문 반환")
async def start_interview(request: InterviewStartRequest):
    """
    면접 유형(e.g., "CS")을 받아, 사전에 로드된 질문 목록에서 무작위로 초기 질문을 반환합니다.
    (이 함수는 매우 빨라서 스레드풀을 사용할 필요가 없습니다.)
    """
    try:
        question = get_random_question()
        return InterviewStartResponse(response=question)
    except Exception as e:
        logger.error(f"/start 엔드포인트 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="초기 질문을 가져오는 중 오류가 발생했습니다.")


@router.post("/next", response_model=InterviewNextResponse, summary="다음 꼬리질문 생성")
async def get_next_question(request: InterviewNextRequest):
    """
    이전 대화 내용을 받아 로컬 LLM을 통해 다음 꼬리 질문을 생성합니다. (비동기 처리)
    """
    try:
        system_message = {"role": "system", "content": config.SYSTEM_PROMPT}
        dialogue_messages = [msg.dict() for msg in request.messages]
        messages_for_model = [system_message] + dialogue_messages
        
        response_text = await run_in_threadpool(
            interview_model.generate_response, 
            messages=messages_for_model, 
            strip_markdown=True
        )
        return InterviewNextResponse(response_text=response_text)
    except Exception as e:
        logger.error(f"/next 엔드포인트 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="꼬리질문 생성 중 오류가 발생했습니다.")


@router.post("/evaluation", response_model=InterviewEvaluationResponse, summary="최종 평가 생성")
async def get_evaluation(request: InterviewEvaluationRequest):
    """
    전체 대화 내용을 받아 로컬 LLM을 통해 구조화된 종합 평가를 생성합니다. (비동기 처리)
    """
    try:
        eval_prompt_messages = interview_model.format_for_evaluation(request.conversation)
        
        report_text = await run_in_threadpool(
            interview_model.generate_response, 
            messages=eval_prompt_messages
        )
        
        logger.info("\n--- LLM Raw Evaluation Report ---\n%s\n---------------------------------\n", report_text)
        
        structured_report = await run_in_threadpool(
            interview_model.parse_evaluation_report, 
            report_text=report_text
        )
        return InterviewEvaluationResponse(evaluation_report=structured_report)
    except Exception as e:
        logger.error(f"/evaluation 엔드포인트 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="최종 평가 생성 중 오류가 발생했습니다.")