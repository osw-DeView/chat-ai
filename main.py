from fastapi import FastAPI
from api import interview
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

app = FastAPI(
    title="CS Interview Assistant API",
    description="CS 면접 꼬리 질문 생성 및 평가를 제공하는 API입니다.",
    version="1.0.0"
)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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