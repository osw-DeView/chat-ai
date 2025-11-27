from fastapi import FastAPI, HTTPException
from crawler.combined import crawl_all_reviews, get_combined_url
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
    기업 이름으로 잡코리아와 사람인에서 면접 후기를 크롤링하는 API

    Args:
        company_name: 기업 이름 (naver, kakao, line, coupang, baemin)

    Returns:
        dict: 통합 크롤링 결과
            - company_name: 회사명
            - reviews: 면접 후기 리스트 (잡코리아 먼저, 사람인 다음)
            - total_reviews: 총 면접 후기 개수
            - jobkorea_count: 잡코리아 후기 개수
            - saramin_count: 사람인 후기 개수
    """
    # URL 확인
    urls = get_combined_url(company_name)
    if not urls:
        raise HTTPException(
            status_code=404,
            detail=f"'{company_name}' 기업을 찾을 수 없습니다. 지원하는 기업: naver, kakao, line, coupang, baemin"
        )

    # 통합 크롤링 실행
    result = crawl_all_reviews(company_name)

    # 완전 실패 시 에러 처리 (두 사이트 모두 실패)
    if result["total_reviews"] == 0 and "errors" in result:
        raise HTTPException(status_code=500, detail=result["errors"])

    return result

app.include_router(interview.router)


