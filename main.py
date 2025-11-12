# main.py

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# 로컬 모듈 임포트 (경로에 맞게 수정 필요)
from models.interview_models import FollowUpRequest, FollowUpResponse, EvaluateRequest, EvaluateResponse
from services.inference import interview_model

logger = logging.getLogger("uvicorn")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI 애플리케이션 시작...")
    if interview_model.model is None:
        logger.error("모델이 로드되지 않았습니다! 서버를 시작할 수 없습니다.")
    yield
    logger.info("FastAPI 애플리케이션 종료.")

app = FastAPI(lifespan=lifespan)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", summary="웹 UI 제공")
async def read_index():
    return FileResponse('index.html')

@app.post("/interview/follow-up", response_model=FollowUpResponse, summary="꼬리질문 생성 (일반 텍스트)")
async def get_follow_up(request: FollowUpRequest):
    try:
        messages_as_dicts = [msg.dict() for msg in request.messages]
        response_text = interview_model.generate_response(messages_as_dicts, strip_markdown=True)
        return FollowUpResponse(response_text=response_text)
    except Exception as e:
        logger.error(f"/follow-up 엔드포인트 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="꼬리질문 생성 중 오류가 발생했습니다.")

@app.post("/interview/evaluate", response_model=EvaluateResponse, summary="최종 평가 생성 (구조화된 JSON)")
async def get_evaluation(request: EvaluateRequest):
    try:
        eval_prompt_messages = interview_model.format_for_evaluation(request.conversation)
        report_text = interview_model.generate_response(eval_prompt_messages)
        
        # 디버깅 로그는 최종 코드에서는 주석 처리하거나 제거할 수 있습니다.
        logger.info("\n--- LLM Raw Evaluation Report ---\n%s\n---------------------------------\n", report_text)
        
        structured_report = interview_model.parse_evaluation_report(report_text)
        return EvaluateResponse(evaluation_report=structured_report)
    except Exception as e:
        logger.error(f"/evaluate 엔드포인트 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="최종 평가 생성 중 오류가 발생했습니다.")