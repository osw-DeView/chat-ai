import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional

def crawl_saramin_reviews(company_url: str) -> Dict:
    """
    사람인에서 면접 후기를 크롤링하는 함수

    Args:
        company_url: 회사별 URL

    Returns:
        dict: 크롤링 결과
            - company_name: 회사명
            - reviews: 면접 후기 리스트
            - total_reviews: 총 면접 후기 개수
            - error: 에러 메시지 (있을 경우)
    """

    # URL 사용
    URL = company_url

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
        html_content = response.text
    except requests.exceptions.RequestException as e:
        return {
            "error": f"웹사이트 요청 중 오류 발생: {str(e)}",
            "company_name": None,
            "reviews": []
        }

    # HTML 파싱
    soup = BeautifulSoup(html_content, 'html.parser')

    # 회사 이름 추출
    company_name_tag = soup.select_one('.hd strong')
    company_name = company_name_tag.text.strip() if company_name_tag else "정보 없음"

    # 면접 후기 리스트 추출
    reviews = []
    review_boxes = soup.select('.box_review')

    for box in review_boxes:
        review_data = {"questions": []}

        # 면접 정보 (면접 유형, 인원, 진행 방식 등)
        info_views = box.select('.info_view')
        for info in info_views:
            title = info.select_one('.tit_view')
            list_items = info.select('.list_item li')

            if title:
                key = title.get_text(strip=True)

                # "면접 질문"은 나중에 qna_pairs로 처리하므로 제외
                if key == "면접 질문":
                    continue

                if list_items:
                    values = [li.get_text(strip=True) for li in list_items]
                    value_str = ', '.join(values)
                else:
                    value_str = info.get_text(strip=True).replace(key, '').strip()

                if value_str:
                    review_data["questions"].append({
                        "question": key,
                        "answer": value_str
                    })

        # 질문 리스트 추출 (면접 질문)
        question_list = box.select('.list_question')
        if question_list:
            questions_in_list = question_list[0].select('li')
            qna_pairs = []
            for li in questions_in_list:
                question_text = li.get_text(strip=True)
                if question_text:
                    qna_pairs.append({
                        "question": question_text,
                        "answer": ""
                    })

            # 면접 질문이 있으면 qna_pairs 형식으로 추가
            if qna_pairs:
                review_data["questions"].append({
                    "question": "면접 질문",
                    "qna_pairs": qna_pairs
                })

        # 평가 정보 (전반적 평가, 난이도, 결과)
        review_dls = box.select('.review')
        for dl in review_dls:
            dt = dl.select_one('dt')
            dd = dl.select_one('dd')
            if dt and dd:
                key = dt.get_text(strip=True)
                value = dd.get_text(strip=True)
                review_data["questions"].append({
                    "question": key,
                    "answer": value
                })

        if review_data["questions"]:
            reviews.append(review_data)

    return {
        "company_name": company_name,
        "reviews": reviews,
        "total_reviews": len(reviews)
    }


# 기업 이름 -> URL 매핑 (영어 키 사용)
SARAMIN_URL_MAP = {
    "naver": "https://www.saramin.co.kr/zf_user/interview-review?my=0&page=1&csn=&group_cd=&orderby=registration&career_cd=&job_category=2&company_nm=%EB%84%A4%EC%9D%B4%EB%B2%84",
    "kakao": "https://www.saramin.co.kr/zf_user/interview-review?my=0&page=1&csn=&group_cd=&orderby=registration&career_cd=&job_category=2&company_nm=%EC%B9%B4%EC%B9%B4%EC%98%A4",
    "line": "https://www.saramin.co.kr/zf_user/interview-review?my=0&page=1&csn=&group_cd=&orderby=registration&career_cd=&job_category=&company_nm=%EB%9D%BC%EC%9D%B8%ED%94%8C%EB%9F%AC%EC%8A%A4",
    "coupang": "https://www.saramin.co.kr/zf_user/interview-review?my=0&page=1&csn=&group_cd=&orderby=registration&career_cd=&job_category=2&company_nm=%EC%BF%A0%ED%8C%A1",
    "baemin": "https://www.saramin.co.kr/zf_user/interview-review?my=0&page=1&csn=&group_cd=&orderby=registration&career_cd=&job_category=&company_nm=%EC%9A%B0%EC%95%84%ED%95%9C%ED%98%95%EC%A0%9C%EB%93%A4"
}


def get_saramin_url(company_name: str) -> Optional[str]:
    """
    기업 이름으로 URL을 찾는 함수

    Args:
        company_name: 기업 이름

    Returns:
        str: URL 또는 None
    """
    return SARAMIN_URL_MAP.get(company_name)
