import requests
from bs4 import BeautifulSoup
import time 

# https://www.jobkorea.co.kr/robots.txt  크롤링 가능한지 참고하기.

# 지금은 특정 회사만 url로 넣어봄, 카카오 모빌리티
URL = "https://www.jobkorea.co.kr/starter/review/view?C_Idx=924&Half_Year_Type_Code=0&Ctgr_Code=3&FavorCo_Stat=0&G_ID=0&Page=1"

try:
    # 사용자 에이전트(User-Agent)를 설정하여 일반 브라우저처럼 보이게 함
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(URL, headers=headers)
    response.raise_for_status() # HTTP 오류 발생 시 예외 처리
    html_content = response.text
except requests.exceptions.RequestException as e:
    print(f"웹사이트 요청 중 오류 발생: {e}")
    exit()

# 혹시 모르니 서버에 과부하 3초 지연
time.sleep(3)


# HTML 내용을 BeautifulSoup 객체로 파싱
soup = BeautifulSoup(html_content, 'html.parser')

# 4. 데이터 추출
print("=" * 40)
print(f"면접 후기 데이터 추출 - 카카오모빌리티 (2020년 하반기 홍보 인턴)")
print("=" * 40)

# 회사 이름 추출
company_name_tag = soup.select_one('.reviewBx .hd strong a')
company_name = company_name_tag.text.strip() if company_name_tag else "정보 없음"
print(f"회사명: {company_name}")


# 개별 질문 및 답변 추출
qna_list = soup.select('.qnaLists .lists li')

for item in qna_list:
    # 각 질문의 제목 (e.g., '1. 면접은 어디에서...')
    question_title_tag = item.select_one('strong')
    
    if question_title_tag and question_title_tag.text.strip().endswith('?'):
        # 일반적인 질문 제목 (1, 2, 3, 4, 6, 7, 8, 9번)
        title = question_title_tag.text.strip()
        content_tag = item.select_one('p')
        content = content_tag.text.strip() if content_tag else "내용 없음"
        
        print(f"[{title}]")
        print(f"  > {content}\n")
    
    elif question_title_tag and question_title_tag.text.strip().startswith('5.'):
        # 5번 질문('면접 질문과 그에 대한 답변')의 세부 Q&A 추출 
        print(f"[{question_title_tag.text.strip()}]")
        
        detail_qnas = item.select('.answer dt, .answer dd')
        current_q = ""
        
        for qa_tag in detail_qnas:
            text = qa_tag.select_one('.t').text.strip() if qa_tag.select_one('.t') else "내용 없음"
            
            if qa_tag.name == 'dt':
                current_q = text
            elif qa_tag.name == 'dd':
                print(f"  - Q: {current_q}")
                print(f"  - A: {text}")
                current_q = "" # Q 초기화
        print() 

print("=" * 40)


