import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, Optional

def crawl_interview_reviews(company_url: str) -> Dict:
    """
    잡코리아에서 면접 후기를 크롤링하는 함수

    Args:
        company_url: 회사별 URL

    Returns:
        dict: 크롤링 결과
            - company_name: 회사명
            - reviews: 면접 후기 리스트
            - error: 에러 메시지 (있을 경우)
    """

    # URL 사용
    URL = company_url

    try:
        # 사용자 에이전트 설정
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

    # 서버 과부하 방지를 위한 지연
    time.sleep(3)

    # HTML 파싱
    soup = BeautifulSoup(html_content, 'html.parser')

    # 회사 이름 추출
    company_name_tag = soup.select_one('.reviewBx .hd strong a')
    company_name = company_name_tag.text.strip() if company_name_tag else "정보 없음"

    # 면접 후기 리스트
    reviews = []
    current_review = None

    # 개별 질문 및 답변 추출
    qna_list = soup.select('.qnaLists .lists li')

    for item in qna_list:
        question_title_tag = item.select_one('strong')

        if question_title_tag:
            title = question_title_tag.text.strip()

            # 1번 질문이면 새로운 면접 후기 시작
            if title.startswith('1.'):
                if current_review:
                    reviews.append(current_review)
                current_review = {"questions": []}

            if title.endswith('?'):
                # 일반 질문 (1, 2, 3, 4, 6, 7, 8, 9번)
                content_tag = item.select_one('p')
                content = content_tag.text.strip() if content_tag else "내용 없음"

                if current_review:
                    current_review["questions"].append({
                        "question": title,
                        "answer": content
                    })

            elif title.startswith('5.'):
                # 5번 질문 (면접 질문과 답변)
                qna_pairs = []
                detail_qnas = item.select('.answer dt, .answer dd')
                current_q = ""

                for qa_tag in detail_qnas:
                    text = qa_tag.select_one('.t').text.strip() if qa_tag.select_one('.t') else "내용 없음"

                    if qa_tag.name == 'dt':
                        current_q = text
                    elif qa_tag.name == 'dd':
                        qna_pairs.append({
                            "question": current_q,
                            "answer": text
                        })
                        current_q = ""

                if current_review:
                    current_review["questions"].append({
                        "question": title,
                        "qna_pairs": qna_pairs
                    })

    # 마지막 리뷰 추가
    if current_review:
        reviews.append(current_review)

    return {
        "company_name": company_name,
        "reviews": reviews,
        "total_reviews": len(reviews)
    }


# 기업 이름 -> URL 템플릿 매핑
COMPANY_URL_MAP = {
    "네이버": "https://www.jobkorea.co.kr/starter/Review/view?C_Idx=215&Half_Year_Type_Code=0&Ctgr_Code=3&FavorCo_Stat=0&G_ID=0&Page=1",
    "카카오": "https://www.jobkorea.co.kr/starter/Review/view?C_Idx=924&Half_Year_Type_Code=0&Ctgr_Code=3&FavorCo_Stat=0&G_ID=0&Page=1",
    "라인": "https://www.jobkorea.co.kr/starter/Review/view?C_Idx=5514&Half_Year_Type_Code=0&Ctgr_Code=3&FavorCo_Stat=0&G_ID=0&Page=1",
    "쿠팡": "https://www.jobkorea.co.kr/starter/review/view?C_Idx=6021&Half_Year_Type_Code=0&Ctgr_Code=3&FavorCo_Stat=0&schTxt=%EC%BF%A0%ED%8C%A1&G_ID=0&Page=1",
    "배달의민족": "https://www.jobkorea.co.kr/starter/review/view?C_Idx=5801&Ctgr_Code=3&FavorCo_Stat=0&schTxt=%EB%B0%B0%EB%8B%AC&G_ID=0&Page=1"
}


def get_company_url(company_name: str) -> Optional[str]:
    """
    기업 이름으로 URL 템플릿을 찾는 함수

    Args:
        company_name: 기업 이름

    Returns:
        str: URL 템플릿 또는 None
    """
    return COMPANY_URL_MAP.get(company_name)


# 직접 실행 시 테스트
if __name__ == "__main__":
    result = crawl_interview_reviews("924", 1)
    print(f"회사명: {result['company_name']}")
    print(f"총 {result['total_reviews']}개의 면접 후기")

    for i, review in enumerate(result['reviews'][:2], 1):
        print(f"\n=== 면접 후기 #{i} ===")
        for q in review['questions'][:3]:
            print(f"[{q['question']}]")
            if 'answer' in q:
                print(f"  > {q['answer'][:50]}...")
