import google.generativeai as genai
from core.config import GEMINI_API_KEY
from models.interview_models import Message
from typing import List, Dict, Any
import json
import re

genai.configure(api_key=GEMINI_API_KEY)

generation_config = {"temperature": 0.7}
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    generation_config=generation_config
)

def generate_tail_question(conversation: List[Message]) -> str:
    """
    이전 대화 내용을 바탕으로 다음 꼬리 질문을 생성합니다.
    """
    prompt = """
    당신은 IT 기업의 숙련된 기술 면접관입니다. 
    아래 대화는 지원자와의 CS 기술 면접 내용입니다. 
    지원자의 마지막 답변을 바탕으로, 그의 지식을 더 깊게 파고들 수 있는 날카로운 꼬리 질문을 '한글로' 그리고 '하나만' 생성해 주세요.
    질문은 간결하고 명확해야 합니다. 다른 부가적인 설명 없이 질문 내용만 반환해주세요.

    [대화 내용]
    {chat_history}
    """.format(chat_history="\n".join([f"{msg.role}: {msg.content}" for msg in conversation]))

    response = model.generate_content(prompt)
    
    return response.text.strip()

def _parse_evaluation_markdown(markdown_text: str) -> Dict[str, Any]:
    """
    LLM이 생성한 마크다운 형식의 평가 텍스트를 파싱하여 딕셔너리로 변환합니다.
    """
    try:
        overall = re.search(r"### 총평\n(.*?)\n###", markdown_text, re.DOTALL).group(1).strip()
        strengths_str = re.search(r"### 잘한 점\n(.*?)\n###", markdown_text, re.DOTALL).group(1).strip()
        weaknesses_str = re.search(r"### 보완할 점\n(.*?)\n###", markdown_text, re.DOTALL).group(1).strip()
        keywords_str = re.search(r"### 부족한 키워드\n(.*?)\n###", markdown_text, re.DOTALL).group(1).strip()
        score_str = re.search(r"### 점수\n(.*?)$", markdown_text, re.DOTALL).group(1).strip()
        score = float(score_str)

        strengths = [s.strip() for s in strengths_str.split('- ') if s.strip()]
        weaknesses = [w.strip() for w in weaknesses_str.split('- ') if w.strip()]
        missing_keywords = [k.strip() for k in keywords_str.split('- ') if k.strip()]

        return {
            "overall_evaluation": overall,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "missing_keywords": missing_keywords,
            "score": score
        }
    except Exception as e:
        print(f"Markdown parsing error: {e}")
        return {
            "overall_evaluation": "평가 결과를 분석하는 데 실패했습니다. LLM이 생성한 원본 텍스트는 다음과 같습니다:\n\n" + markdown_text,
            "strengths": [],
            "weaknesses": [],
            "missing_keywords": [],
            "score": 0.0
        }

def evaluate_conversation(conversation: List[Message]) -> Dict[str, Any]:
    """
    전체 대화 내용을 바탕으로 면접을 평가하고, LLM이 생성한 마크다운을 파싱하여 JSON으로 반환합니다.
    """
    prompt = """
    당신은 지원자의 기술적 깊이를 평가하는 IT 전문 면접관입니다.
    다음은 한 지원자와의 전체 CS 기술 면접 대화록입니다.
    이 대화 내용을 바탕으로 지원자의 CS 지식을 평가하고, 아래 마크다운 형식을 '반드시' 준수하여 '한글로' 응답해 주세요.

    [대화 내용]
    {chat_history}

    [출력 형식]
    ### 총평
    (지원자의 답변에 대한 전반적인 평가를 마크다운 형식으로 자유롭게 작성. 예를 들어 **강조**나 *기울임* 사용 가능)

    ### 잘한 점
    - (잘한 점 1: 구체적인 강점 요약)
    - (잘한 점 2)

    ### 보완할 점
    - (보완할 점 1: 구체적인 약점 및 개선 방향 제시)
    - (보완할 점 2)

    ### 부족한 키워드
    - (답변에서 누락된 중요 기술 키워드 1)
    - (키워드 2)

    ### 점수
    (100점 만점 기준의 점수를 다른 설명 없이 숫자로만 표시. 예: 85.5)
    """.format(chat_history="\n".join([f"{msg.role}: {msg.content}" for msg in conversation])) # 점수 기준만 100점으로 변경

    response = model.generate_content(prompt)
    markdown_response = response.text.strip()
    
    return _parse_evaluation_markdown(markdown_response)