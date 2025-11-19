from fastapi import FastAPI, HTTPException
from crawler.job import crawl_interview_reviews, get_company_url

app = FastAPI(
    title="CS Interview Assistant API"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the CS Interview Assistant API"}


@app.get("/api/interview-reviews")
def get_interview_reviews(company_name: str):
    """
    기업 이름으로 면접 후기를 크롤링하는 API

    Args:
        company_name: 기업 이름 (네이버, 카카오, 라인, 쿠팡, 배달의민족)

    Returns:
        dict: 크롤링 결과
    """
    # 기업 이름으로 URL 찾기
    company_url = get_company_url(company_name)

    if not company_url:
        raise HTTPException(
            status_code=404,
            detail=f"'{company_name}' 기업을 찾을 수 없습니다. 지원하는 기업: 네이버, 카카오, 라인, 쿠팡, 배달의민족"
        )

    # 크롤링 실행
    result = crawl_interview_reviews(company_url)

    # 에러 처리
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result