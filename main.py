from fastapi import FastAPI, HTTPException
from crawler.job import crawl_interview_reviews, get_company_url
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

@app.get("/", include_in_schema=False)
async def root_redirect():
    """
    루트 경로 접속 시 API 문서(/docs)로 리디렉션합니다.
    """
    return RedirectResponse(url="/docs")


@app.get("/api/interview-reviews")
def get_interview_reviews(company_name: str):
    """
    기업 이름으로 면접 후기를 크롤링하는 API

    Args:
        company_name: 기업 이름 (naver, kakao, line, coupang, baemin)

    Returns:
        dict: 크롤링 결과
    """
    # 기업 이름으로 URL 찾기
    company_url = get_company_url(company_name)

    if not company_url:
        raise HTTPException(
            status_code=404,
            detail=f"'{company_name}' 기업을 찾을 수 없습니다. 지원하는 기업: naver, kakao, line, coupang, baemin"
        )

    # 크롤링 실행
    result = crawl_interview_reviews(company_url)

    # 에러 처리
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result

app.include_router(interview.router)


