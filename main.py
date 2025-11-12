from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

from api import interview
from services.inference import interview_model

logger = logging.getLogger("uvicorn")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 애플리케이션의 시작과 종료 시점에 실행될 로직을 정의합니다.
    """
    logger.info("FastAPI 애플리케이션 시작...")
    yield
    
    logger.info("FastAPI 애플리케이션 종료.")

app = FastAPI(
    title="Local Interview LLM API",
    description="로컬 LLM을 활용한 CS 면접 꼬리 질문 생성 및 평가 API",
    version="2.0.0",
    lifespan=lifespan 
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview.router)

@app.get("/", include_in_schema=False)
async def root_redirect():
    """
    루트 경로 접속 시 API 문서(/docs)로 리디렉션합니다.
    """
    return RedirectResponse(url="/docs")