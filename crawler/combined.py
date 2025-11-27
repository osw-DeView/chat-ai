from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    # main.py에서 import할 때
    from crawler.job import crawl_interview_reviews as crawl_jobkorea, get_company_url
    from crawler.saramin import crawl_saramin_reviews, get_saramin_url
except ImportError:
    # crawler 디렉토리에서 직접 실행할 때
    from job import crawl_interview_reviews as crawl_jobkorea, get_company_url
    from saramin import crawl_saramin_reviews, get_saramin_url


def crawl_all_reviews(company_name: str) -> Dict:
    """
    잡코리아와 사람인에서 면접 후기를 동시에 크롤링하는 함수

    Args:
        company_name: 기업 이름 (영어 키: naver, kakao, line, coupang, baemin)

    Returns:
        dict: 통합 크롤링 결과
            - company_name: 회사명
            - reviews: 면접 후기 리스트 (잡코리아 먼저, 사람인 다음)
            - total_reviews: 총 면접 후기 개수
            - jobkorea_count: 잡코리아 후기 개수
            - saramin_count: 사람인 후기 개수
            - error: 에러 메시지 (있을 경우)
    """

    company_name_result = None
    jobkorea_count = 0
    saramin_count = 0
    errors = []

    # URL 확인
    jobkorea_url = get_company_url(company_name)
    saramin_url = get_saramin_url(company_name)

    # 병렬 크롤링 실행
    jobkorea_result = None
    saramin_result = None

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {}

        # 잡코리아 크롤링 시작
        if jobkorea_url:
            futures['jobkorea'] = executor.submit(crawl_jobkorea, jobkorea_url)
        else:
            errors.append("잡코리아: URL을 찾을 수 없습니다")

        # 사람인 크롤링 시작
        if saramin_url:
            futures['saramin'] = executor.submit(crawl_saramin_reviews, saramin_url)
        else:
            errors.append("사람인: URL을 찾을 수 없습니다")

        # 결과 수집 (순서 보장을 위해 직접 접근)
        if 'jobkorea' in futures:
            try:
                jobkorea_result = futures['jobkorea'].result()
            except Exception as e:
                errors.append(f"잡코리아: {str(e)}")

        if 'saramin' in futures:
            try:
                saramin_result = futures['saramin'].result()
            except Exception as e:
                errors.append(f"사람인: {str(e)}")

    # 결과 병합 (순서 유지: 잡코리아 먼저, 사람인 다음)
    all_reviews = []

    # 1. 잡코리아 결과 추가
    if jobkorea_result:
        if "error" not in jobkorea_result:
            all_reviews.extend(jobkorea_result.get("reviews", []))
            jobkorea_count = jobkorea_result.get("total_reviews", 0)
            if not company_name_result and jobkorea_result.get("company_name"):
                company_name_result = jobkorea_result.get("company_name")
        else:
            errors.append(f"잡코리아: {jobkorea_result['error']}")

    # 2. 사람인 결과 추가
    if saramin_result:
        if "error" not in saramin_result:
            all_reviews.extend(saramin_result.get("reviews", []))
            saramin_count = saramin_result.get("total_reviews", 0)
            if not company_name_result and saramin_result.get("company_name"):
                company_name_result = saramin_result.get("company_name")
        else:
            errors.append(f"사람인: {saramin_result['error']}")

    # 결과 반환
    result = {
        "company_name": company_name_result or "정보 없음",
        "reviews": all_reviews,
        "total_reviews": len(all_reviews),
        "jobkorea_count": jobkorea_count,
        "saramin_count": saramin_count
    }

    if errors:
        result["errors"] = errors

    return result


def get_combined_url(company_name: str) -> Optional[Dict[str, str]]:
    """
    기업 이름으로 잡코리아와 사람인 URL을 찾는 함수

    Args:
        company_name: 기업 이름

    Returns:
        dict: URL 정보 또는 None
            - jobkorea: 잡코리아 URL
            - saramin: 사람인 URL
    """
    jobkorea_url = get_company_url(company_name)
    saramin_url = get_saramin_url(company_name)

    if jobkorea_url or saramin_url:
        return {
            "jobkorea": jobkorea_url,
            "saramin": saramin_url
        }
    return None
