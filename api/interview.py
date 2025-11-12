# api/interview.py

from fastapi import APIRouter, HTTPException
import logging

# 로컬 모듈 임포트
from models.interview_models import (
    InterviewStartRequest, InterviewStartResponse,
    InterviewNextRequest, InterviewNextResponse,
    InterviewEvaluationRequest, InterviewEvaluationResponse
)
from services.inference import interview_model         # 기존 로컬 LLM 추론 서비스
from services.initial_questions import get_random_question # 2단계에서 추가한 초기 질문 서비스
from core import config                                    # 시스템 프롬프트 등을 담고 있는 설정

# APIRouter 인스턴스 생성
# 이 라우터에 정의된 모든 경로는 자동으로 "/interview" 접두사를 갖게 됩니다.
router = APIRouter(
    prefix="/interview",
    tags=["Interview API"]  # Swagger UI에서 API를 그룹화하는 태그
)

# uvicorn 로거를 사용하여 로그를 남깁니다.
logger = logging.getLogger("uvicorn")

@router.post("/start", response_model=InterviewStartResponse, summary="면접 시작 및 초기 질문 반환")
async def start_interview(request: InterviewStartRequest):
    """
    면접 유형(e.g., "CS")을 받아, 사전에 로드된 질문 목록에서 무작위로 초기 질문을 반환합니다.
    """
    try:
        # request.interviewType은 향후 다른 유형의 면접(e.g., "FE", "BE")을 추가할 경우를 대비해
        # 미리 API 명세에 포함시켜 둔 것입니다. 현재는 사용되지 않습니다.
        question = get_random_question()
        return InterviewStartResponse(response=question)
    except Exception as e:
        logger.error(f"/start 엔드포인트 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="초기 질문을 가져오는 중 오류가 발생했습니다.")


@router.post("/next", response_model=InterviewNextResponse, summary="다음 꼬리질문 생성")
async def get_next_question(request: InterviewNextRequest):
    """
    이전 대화 내용을 받아 로컬 LLM을 통해 다음 꼬리 질문을 생성합니다.
    """
    try:
        # 1. 서버에서 시스템 프롬프트를 정의합니다.
        system_message = {"role": "system", "content": config.SYSTEM_PROMPT}
        
        # 2. 클라이언트로부터 받은 대화 기록을 가져옵니다.
        dialogue_messages = [msg.dict() for msg in request.messages]
        
        # 3. 시스템 프롬프트와 대화 기록을 합쳐 모델에 전달할 최종 입력을 만듭니다.
        messages_for_model = [system_message] + dialogue_messages
        
        # 4. 모델 서비스를 호출하여 응답을 생성합니다.
        response_text = interview_model.generate_response(messages_for_model, strip_markdown=True)
        return InterviewNextResponse(response_text=response_text)
    except Exception as e:
        logger.error(f"/next 엔드포인트 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="꼬리질문 생성 중 오류가 발생했습니다.")


@router.post("/evaluation", response_model=InterviewEvaluationResponse, summary="최종 평가 생성")
async def get_evaluation(request: InterviewEvaluationRequest):
    """
    전체 대화 내용을 받아 로컬 LLM을 통해 구조화된 종합 평가를 생성합니다.
    """
    try:
        # 1. 평가용 프롬프트 형식으로 대화 기록을 변환합니다.
        eval_prompt_messages = interview_model.format_for_evaluation(request.conversation)
        
        # 2. 모델 서비스를 호출하여 마크다운 형식의 평가 리포트를 생성합니다.
        report_text = interview_model.generate_response(eval_prompt_messages)
        
        # 디버깅을 위해 모델이 생성한 원본 텍스트를 로그로 남깁니다.
        logger.info("\n--- LLM Raw Evaluation Report ---\n%s\n---------------------------------\n", report_text)
        
        # 3. 마크다운 리포트를 구조화된 JSON 객체로 파싱합니다.
        structured_report = interview_model.parse_evaluation_report(report_text)
        return InterviewEvaluationResponse(evaluation_report=structured_report)
    except Exception as e:
        logger.error(f"/evaluation 엔드포인트 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="최종 평가 생성 중 오류가 발생했습니다.")