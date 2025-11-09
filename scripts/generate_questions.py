import os
import csv
import time
import re
from typing import Dict, List, Any

import google.generativeai as genai
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")
genai.configure(api_key=API_KEY)

generation_config = {"temperature": 0.7}
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    generation_config=generation_config
)

QUESTIONS_PER_GROUP = 5

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV_PATH = os.path.join(SCRIPT_DIR, '..', 'data', '학습컨텐츠데이터-종합 (1).csv')
OUTPUT_CSV_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'cs_questions.csv')

FILTER_KEYWORDS = ["참고 자료", "주요 질문", "정리", "란?"]

PROMPT_TEMPLATE = """
당신은 IT 기업의 숙련된 기술 면접관입니다. 당신의 임무는 주어진 주제 그룹을 대표하는 깊이 있는 기술 면접 질문을 생성하는 것입니다.

[지시사항]
1. 아래 [주요 토픽] 목록을 종합적으로 참고하여, 이 주제 그룹 전체를 아우르는 심층적인 기술 면접 질문을 **{num_questions}개** 생성해주세요.
2. 질문은 단순히 특정 토픽의 정의를 묻는 것을 넘어, 여러 토픽을 연결하거나, 개념의 **장단점, 비교, 특정 상황에서의 활용법, 동작 원리** 등을 묻는 질문이어야 합니다.
3. 전체 결과를 반드시 아래 [출력 형식]과 같이 번호가 매겨진 마크다운 리스트 형식으로만 반환해주세요. 다른 부가적인 설명은 절대 추가하지 마세요.

[주요 토픽]
{topic_titles}

[출력 형식]
1. 생성된 첫 번째 면접 질문
2. 생성된 두 번째 면접 질문
...
"""

def load_and_group_data() -> Dict[str, List[Dict[str, str]]]:
    """
    입력 CSV 파일을 읽고 'second_category'를 기준으로 데이터를 그룹화합니다.
    """
    grouped_data = {}
    print(f"'{INPUT_CSV_PATH}' 파일에서 데이터 로드를 시작합니다...")
    try:
        with open(INPUT_CSV_PATH, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                title = row.get('title', '').strip()
                if not title or any(keyword in title for keyword in FILTER_KEYWORDS):
                    continue
                second_category = row.get('second_category', '기타').strip()
                if second_category not in grouped_data:
                    grouped_data[second_category] = []
                grouped_data[second_category].append({
                    "first_category": row.get('first_category', '').strip(),
                    "title": title,
                })
        print(f"총 {len(grouped_data)}개의 주제 그룹을 로드했습니다.")
        return grouped_data
    except FileNotFoundError:
        print(f"오류: 입력 파일 '{INPUT_CSV_PATH}'을(를) 찾을 수 없습니다.")
        return {}
    except Exception as e:
        print(f"데이터 로드 중 오류 발생: {e}")
        return {}


def generate_questions_for_group(topics: List[Dict[str, str]], num_questions: int) -> str:
    """
    한 그룹의 토픽 데이터를 받아 Gemini API를 호출하고 마크다운 응답을 반환합니다.
    """
    topic_titles = "\n".join([f"- {topic['title']}" for topic in topics])

    prompt = PROMPT_TEMPLATE.format(
        num_questions=num_questions,
        topic_titles=topic_titles
    )

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"\nGemini API 호출 중 오류 발생: {e}")
        return ""


def parse_and_save_questions(
    writer: Any,
    markdown_text: str,
    category: str
) -> int:
    """
    번호 매기기 마크다운 텍스트를 파싱하여 CSV 파일에 저장하고, 저장된 질문 수를 반환합니다.
    """
    count = 0
    questions = re.findall(r"^\s*\d+\.\s*(.*)", markdown_text, re.MULTILINE)

    for question in questions:
        if question:
            writer.writerow([category, question.strip()])
            count += 1
    return count


def main():
    """
    메인 실행 함수
    """
    print("=" * 50)
    print("Gemini API를 이용한 면접 질문 자동 생성 스크립트")
    print(f"그룹당 생성 목표 질문 수: {QUESTIONS_PER_GROUP}")
    print("=" * 50)

    grouped_data = load_and_group_data()
    if not grouped_data:
        print("처리할 데이터가 없습니다. 스크립트를 종료합니다.")
        return

    total_questions_generated = 0

    try:
        with open(OUTPUT_CSV_PATH, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.writer(f_out)
            writer.writerow(['category', 'question'])
    except IOError as e:
        print(f"오류: 출력 파일 '{OUTPUT_CSV_PATH}'을(를) 열 수 없습니다. {e}")
        return

    print("\n질문 생성을 시작합니다...")
    for second_category, topics in tqdm(grouped_data.items(), desc="주제 그룹 처리 중"):
        if not topics:
            continue
        first_category = topics[0]['first_category']

        markdown_response = generate_questions_for_group(topics, QUESTIONS_PER_GROUP)

        if not markdown_response:
            tqdm.write(f"'{second_category}' 그룹에 대한 질문 생성에 실패했습니다. (API 응답 없음)")
            continue

        with open(OUTPUT_CSV_PATH, 'a', newline='', encoding='utf-8') as f_out:
            writer = csv.writer(f_out)
            count = parse_and_save_questions(writer, markdown_response, first_category)
            if count > 0:
                total_questions_generated += count
            else:
                tqdm.write(f"경고: '{second_category}' 그룹에 대해 파싱할 수 있는 질문이 없습니다.")

        time.sleep(1)

    print("\n" + "=" * 50)
    print("질문 생성이 완료되었습니다!")
    print(f"총 생성된 질문 수: {total_questions_generated}")
    print(f"결과가 '{OUTPUT_CSV_PATH}' 파일에 저장되었습니다.")
    print("=" * 50)


if __name__ == "__main__":
    main()