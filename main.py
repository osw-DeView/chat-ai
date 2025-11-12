from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
    
    interview_model.load_gguf_model()
    
    if interview_model.model is None:
        logger.error("모델이 로드되지 않았습니다! 서버를 시작할 수 없습니다.")
    
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

static_dir = "static"
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def read_index():
        """
        루트 경로('/') 접속 시 static/index.html 파일을 반환합니다.
        """
        return FileResponse(os.path.join(static_dir, 'index.html'))
else:
    logger.warning(f"'{static_dir}' 폴더를 찾을 수 없습니다. 정적 파일 서비스가 비활성화됩니다.")

    @app.get("/", include_in_schema=False)
    async def read_root():
        return {"message": "Local Interview LLM API에 오신 것을 환영합니다. API 문서는 /docs 경로를 확인하세요."}